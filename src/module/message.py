import base64
import random
import re

from botpy import BotAPI
from botpy.message import Message, GroupMessage, C2CMessage

from src.core.constants import Constants
from src.core.exception import handle_exception
from src.core.tools import run_async


class RobotMessage:
    def __init__(self, api: BotAPI):
        self.api = api
        self.guild_public = False
        self.guild_message = None
        self.group_message = None
        self.c2c_message = None
        self.content = ""
        self.tokens = ""
        self.author_id = ""
        self.attachments = []
        self.msg_seq = 0
        self.user_permission_level = 0
        self.main_event_loop = None

    def setup_guild_message(self, main_event_loop, message: Message, is_public: bool = False):
        self.main_event_loop = main_event_loop
        self.guild_public = is_public
        self.guild_message = message
        self.content = message.content
        self.tokens = re.sub(r'<@!\d+>', '', message.content).strip().split()
        self.author_id = message.author.__dict__['id']
        self.attachments = message.attachments
        self.msg_seq = 0
        self.user_permission_level = 2 if self.author_id in Constants.config['admin_qq_id'] else \
            1 if self.author_id in Constants.config['mod_qq_id'] else 0

    def setup_group_message(self, main_event_loop, message: GroupMessage):
        self.main_event_loop = main_event_loop
        self.group_message = message
        self.content = message.content
        self.tokens = re.sub(r'<@!\d+>', '', message.content).strip().split()
        self.author_id = message.author.__dict__['member_openid']
        self.attachments = message.attachments
        self.msg_seq = 0
        self.user_permission_level = 2 if self.author_id in Constants.config['admin_qq_id'] else \
            1 if self.author_id in Constants.config['mod_qq_id'] else 0

    def setup_c2c_message(self, main_event_loop, message: C2CMessage):
        self.main_event_loop = main_event_loop
        self.c2c_message = message
        self.content = message.content
        self.tokens = re.sub(r'<@!\d+>', '', message.content).strip().split()
        self.author_id = message.author.__dict__['user_openid']
        self.attachments = message.attachments
        self.msg_seq = 0
        self.user_permission_level = 2 if self.author_id in Constants.config['admin_qq_id'] else \
            1 if self.author_id in Constants.config['mod_qq_id'] else 0

    async def reply(self, content: str, img_path: str = None, img_url: str = None, modal_words: bool = True):
        if modal_words:  # 加点语气词
            chosen_modal_word = random.choice(Constants.modal_words)
            content += chosen_modal_word

        self.msg_seq += 1
        if self.guild_message:  # 频道消息
            run_async(self.main_event_loop,
                      self.api.post_message(
                          channel_id=self.guild_message.channel_id, msg_id=self.guild_message.id,
                          content=f"<@{self.guild_message.author.id}>{content}",
                          file_image=img_path, image=img_url))
        elif self.group_message:  # 群消息
            if img_path is not None or img_url is not None:
                media = None
                retry_times = 0
                while media is None and retry_times < 3:
                    if img_path is not None:
                        with open(img_path, "rb") as img:
                            file_image = img.read()
                        media = run_async(self.main_event_loop,
                                          self.api.post_group_file(
                                              group_openid=self.group_message.group_openid,
                                              file_type=1,
                                              file_data=base64.b64encode(file_image).decode('UTF-8'))
                                          )
                    else:
                        media = run_async(self.main_event_loop,
                                          self.api.post_group_file(
                                              group_openid=self.group_message.group_openid,
                                              file_type=1,
                                              url=img_url)
                                          )
                    retry_times += 1

                if media is None:
                    run_async(self.main_event_loop,
                              self.api.post_group_message(
                                  group_openid=self.group_message.group_openid,
                                  msg_type=0, msg_id=self.group_message.id,
                                  content="发送图片失败，请稍后重试", msg_seq=self.msg_seq)
                              )
                else:
                    run_async(self.main_event_loop,
                              self.api.post_group_message(
                                  group_openid=self.group_message.group_openid,
                                  msg_type=7, msg_id=self.group_message.id,
                                  content=content, media=media, msg_seq=self.msg_seq)
                              )
            else:
                run_async(self.main_event_loop,
                          self.api.post_group_message(
                              group_openid=self.group_message.group_openid,
                              msg_type=0, msg_id=self.group_message.id,
                              content=content, msg_seq=self.msg_seq)
                          )
        elif self.c2c_message:  # 私聊消息
            if img_path is not None or img_url is not None:
                media = None
                retry_times = 0
                while media is None and retry_times < 3:
                    if img_path is not None:
                        with open(img_path, "rb") as img:
                            file_image = img.read()
                        media = run_async(self.main_event_loop,
                                          self.api.post_c2c_file(
                                              openid=self.author_id,
                                              file_type=1,
                                              file_data=base64.b64encode(file_image).decode('UTF-8'))
                                          )
                    else:
                        media = run_async(self.main_event_loop,
                                          self.api.post_c2c_file(
                                              openid=self.author_id,
                                              file_type=1,
                                              url=img_url)
                                          )
                    retry_times += 1

                if media is None:
                    run_async(self.main_event_loop,
                              self.api.post_c2c_message(
                                  openid=self.author_id,
                                  msg_type=0,
                                  msg_id=self.c2c_message.id,
                                  content="发送图片失败，请稍后重试",
                                  msg_seq=self.msg_seq)
                              )
                else:
                    run_async(self.main_event_loop,
                              self.api.post_c2c_message(
                                  openid=self.author_id,
                                  msg_type=7,
                                  msg_id=self.c2c_message.id,
                                  content=content,
                                  media=media,
                                  msg_seq=self.msg_seq)
                              )
            else:
                run_async(self.main_event_loop,
                          self.api.post_c2c_message(
                              openid=self.author_id,
                              msg_type=0,
                              msg_id=self.c2c_message.id,
                              content=content,
                              msg_seq=self.msg_seq)
                          )
        else:  # 其他未支持的消息类型
            return


async def report_exception(message: RobotMessage, module_name: str, trace: str, e: Exception):
    Constants.log.warn(f"[Operation failed] in module {module_name}.\n{repr(e)}")
    Constants.log.error(trace)
    await message.reply(handle_exception(e), modal_words=False)
