from utils.interact import RobotMessage
from utils.tools import fetch_json

__hitokoto_version__ = "v1.0.1"

__hitokoto_help_content__ = """/hitokoto: 获取一条一言。指令别名：/一言，/来(一)句(话)"""


async def reply_hitokoto(message: RobotMessage):
    json = fetch_json("https://v1.hitokoto.cn/")
    content = json['hitokoto']
    where = json['from']
    author = json['from_who'] if json['from_who'] else ""
    await message.reply(f"[Hitokoto]\n{content}\nBy {author}「{where}」", modal_words=False)
