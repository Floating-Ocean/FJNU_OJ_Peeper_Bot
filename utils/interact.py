import base64
import os
import random
import re

from botpy import BotAPI
from botpy.ext.cog_yaml import read
from botpy.message import Message, GroupMessage

_config = read(os.path.join(os.path.join(os.path.dirname(__file__), ".."), "config.yaml"))
__interact_version__ = "v2.1.3"

_key_words = {
    "傻逼": ["谢谢夸奖", "反弹", "可能还真被你说对了", "嗯", "好的", "哼，你才是"],
    "性别": ["盲猜我的性别是武装直升机", "我也不知道我的性别是啥"],
    "干嘛": ["how", "what", "which", "why", "whether", "when"],
    "谢谢": ["qaq", "不用谢qaq", "qwq"],
    "qaq": ["qwq"],
    "你是谁": ["猜猜我是谁", "我也不知道", "你是谁"],
    "省": ["妈妈生的", "一眼丁真"],
    "似": ["看上去我还活着", "似了"]
}

_modal_words = ["喵", "呢", "捏", "qaq"]


class RobotMessage:
    def __init__(self, api: BotAPI):
        self.api = api
        self.guild = False
        self.guild_message = None
        self.group_message = None
        self.content = ""
        self.pure_content = ""
        self.author_id = ""
        self.attachments = []
        self.msg_seq = 0
        self.user_permission_level = 0

    def setup_guild_message(self, message: Message):
        self.guild = True
        self.guild_message = message
        self.content = message.content
        self.pure_content = self.content
        self.author_id = message.author.__dict__['id']
        self.attachments = message.attachments
        self.msg_seq = 0

    def setup_group_message(self, message: GroupMessage):
        self.guild = False
        self.group_message = message
        self.content = message.content
        self.pure_content = re.sub(r'<@!\d+>', '', message.content).strip().split()
        self.author_id = message.author.__dict__['member_openid']
        self.attachments = message.attachments
        self.msg_seq = 0
        self.user_permission_level = 2 if self.author_id in _config['admin_qq_id'] else 1 if self.author_id in \
                                                                                             _config[
                                                                                           'mod_qq_id'] else 0

    async def reply(self, content: str, img_path: str = None, img_url: str = None, modal_words: bool = True):
        if modal_words:  # 加点语气词
            content += random.choice(_modal_words)

        self.msg_seq += 1
        if self.guild:  # 频道消息
            await self.api.post_message(channel_id=self.guild_message.channel_id, msg_id=self.guild_message.id,
                                        content=f"<@{self.guild_message.author.id}>{content}", file_image=img_path,
                                        image=img_url)
        else:  # 群消息
            if img_path is not None or img_url is not None:
                media = None
                retry_times = 0

                while media is None and retry_times < 3:
                    if img_path is not None:
                        with open(img_path, "rb") as img:
                            file_image = img.read()
                        media = await self.api.post_group_file(
                            group_openid=self.group_message.group_openid,
                            file_type=1,
                            file_data=base64.b64encode(file_image).decode('UTF-8'),
                        )
                    else:
                        media = await self.api.post_group_file(
                            group_openid=self.group_message.group_openid,
                            file_type=1,
                            url=img_url,
                        )
                    retry_times += 1

                if media is None:
                    await self.api.post_group_message(
                        group_openid=self.group_message.group_openid,
                        msg_type=0,
                        msg_id=self.group_message.id,
                        content="发送图片失败，请稍后重试",
                        msg_seq=self.msg_seq
                    )
                else:
                    await self.api.post_group_message(
                        group_openid=self.group_message.group_openid,
                        msg_type=7,
                        msg_id=self.group_message.id,
                        content=content,
                        media=media,
                        msg_seq=self.msg_seq
                    )
            else:
                await self.api.post_group_message(
                    group_openid=self.group_message.group_openid,
                    msg_type=0,
                    msg_id=self.group_message.id,
                    content=content,
                    msg_seq=self.msg_seq
                )


def match_key_words(content: str) -> str:
    for each in _key_words:
        if each in content:
            return random.choice(_key_words[each])
    return random.choice(["你干嘛", "咋了", "how", "what"])
