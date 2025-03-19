import asyncio
import base64
import random
import re
from asyncio import AbstractEventLoop
from enum import Enum
from typing import Optional, Union

from botpy import BotAPI
from botpy.message import Message, GroupMessage, C2CMessage

from src.core.constants import Constants
from src.core.exception import handle_exception


class MessageType(Enum):
    GUILD = "guild"
    GROUP = "group"
    C2C = "c2c"


class PermissionLevel(Enum):
    USER = 0
    MOD = 1
    ADMIN = 2


class RobotMessage:
    """合并多种消息类型的操作"""
    def __init__(self, api: BotAPI):
        self.api = api
        self.message_type: Optional[MessageType] = None
        self.message: Optional[Union[Message, GroupMessage, C2CMessage]] = None
        self.loop = None

        self.content = ""
        self.tokens = []
        self.author_id = ""
        self.attachments = []
        self.msg_seq = 0
        self.user_permission_level: PermissionLevel = PermissionLevel.USER
        self._public = False  # Guild only

    def is_guild_public(self):
        return self._public

    def _initial_setup(self, message: Message | GroupMessage | C2CMessage, author_id_path: str):
        self.content = message.content
        self.tokens = re.sub(r'<@!\d+>', '', message.content).strip().split()
        self.author_id = getattr(message.author, author_id_path, "")
        self.attachments = message.attachments
        self._set_user_permission()

    def _set_user_permission(self):
        """统一设置用户权限等级"""
        config = Constants.config
        self.user_permission_level = (
            PermissionLevel.ADMIN if self.author_id in config['admin_qq_id'] else
            PermissionLevel.MOD if self.author_id in config['mod_qq_id'] else
            PermissionLevel.USER
        )

    def setup_guild_message(self, loop: AbstractEventLoop, message: Message, is_public: bool = False):
        self.loop = loop
        self.message_type = MessageType.GUILD
        self.message = message
        self._public = is_public
        self._initial_setup(message, 'id')

    def setup_group_message(self, loop: AbstractEventLoop, message: GroupMessage):
        self.loop = loop
        self.message_type = MessageType.GROUP
        self.message = message
        self._initial_setup(message, 'member_openid')

    def setup_c2c_message(self, loop: AbstractEventLoop, message: C2CMessage):
        self.loop = loop
        self.message_type = MessageType.C2C
        self.message = message
        self._initial_setup(message, 'user_openid')

    def reply(self, content: str, img_path: str = None, img_url: str = None, modal_words: bool = True):
        """异步发送回复的入口方法"""
        if not self.loop:
            raise RuntimeError("Event loop not initialized")

        friendly_content = content + random.choice(Constants.modal_words) if modal_words else content

        asyncio.run_coroutine_threadsafe(  # 不能使用 loop.create_task，会造成资源竞争
            self._send_message(friendly_content, img_path, img_url),
            self.loop
        )

    async def _send_message(self, content: str, img_path: str, img_url: str):
        """统一消息发送入口"""
        Constants.log.info(f"Initiated reply: {content}")
        self.msg_seq += 1

        # 处理媒体文件上传
        media = await self._upload_media(img_path, img_url) \
            if (img_path or img_url) and self.message_type != MessageType.GUILD else None

        base_params = await self._pack_message_params(content, media)
        if not base_params:
            return
        params = base_params

        # 频道api只需传递参数
        if self.message_type == MessageType.GUILD:
            params = {**base_params, 'file_image': img_path, 'image': img_url}

        await self._handle_send_request(params)

    async def _upload_media(self, img_path: str, img_url: str) -> dict:
        """带重试机制的媒体上传"""
        for _ in range(3):  # 最多重试3次
            try:
                if img_path:
                    with open(img_path, "rb") as f:
                        file_data = base64.b64encode(f.read()).decode()
                    received_media = await self._call_upload_api(file_data=file_data)
                else:
                    received_media = await self._call_upload_api(url=img_url)
                if received_media['status'] == 'ok':
                    return received_media
            except Exception as e:
                Constants.log.warn(f"Media upload failed: {e}")
        return {'status': 'error', 'data': None}

    async def _call_upload_api(self, **kwargs) -> dict:
        """调用对应的文件上传API"""
        if self.message_type == MessageType.GUILD:
            raise TypeError("No need to upload images for guild messages.")

        method_map = {
            MessageType.GROUP: self.api.post_group_file,
            MessageType.C2C: self.api.post_c2c_file
        }
        common_args = {
            "file_type": 1,
            **kwargs
        }

        if self.message_type == MessageType.GROUP:
            common_args["group_openid"] = self.message.group_openid
        elif self.message_type == MessageType.C2C:
            common_args["openid"] = self.author_id

        received_media = await method_map[self.message_type](**common_args)
        if received_media:
            return {'status': 'ok', 'data': received_media}
        else:
            return {'status': 'error', 'data': None}

    async def _pack_message_params(self, content: str, media: Optional[dict]) -> Optional[dict]:
        """构造消息发送参数"""
        base_params = {
            "content": content,
            "msg_id": self.message.id,
            "msg_seq": self.msg_seq
        }

        # 媒体消息
        if media:
            if media['status'] != 'ok':
                await self._send_fallback_message("发送图片失败，请稍后重试")
                return None
            return {**base_params, "msg_type": 7, "media": media['data']}

        # 文本消息
        return {**base_params, "msg_type": 0}

    async def _handle_send_request(self, params: dict):
        """分发到具体的发送方法"""
        intended_params_name = ['content', 'embed', 'ark', 'message_reference',
                                'msg_id', 'event_id', 'markdown', 'keyboard']
        if self.message_type == MessageType.GUILD:
            params['content'] = f"<@{self.message.author.id}>{params['content']}"
            params['channel_id'] = self.message.channel_id
            intended_params_name.extend(['channel_id', 'image', 'file_image'])
            api_method = self.api.post_message
        elif self.message_type == MessageType.GROUP:
            params['group_openid'] = self.message.group_openid
            intended_params_name.extend(['group_openid', 'msg_type', 'media', 'msg_seq'])
            api_method = self.api.post_group_message
        else:
            params['openid'] = self.author_id
            intended_params_name.extend(['openid', 'msg_type', 'media', 'msg_seq'])
            api_method = self.api.post_c2c_message

        intended_params = {name: params[name] for name in intended_params_name if name in params}
        await api_method(**intended_params)

    async def _send_fallback_message(self, text: str):
        """发送失败回退消息"""
        fallback_params = {
            "msg_type": 0,
            "content": text,
            "msg_id": self.message.id,
            "msg_seq": self.msg_seq
        }
        await self._handle_send_request(fallback_params)

    def report_exception(self, module_name: str, trace: str, e: Exception):
        Constants.log.warn(f"[Operation failed] in module {module_name}.\n{repr(e)}")
        Constants.log.error(trace)
        self.reply(handle_exception(e), modal_words=False)
