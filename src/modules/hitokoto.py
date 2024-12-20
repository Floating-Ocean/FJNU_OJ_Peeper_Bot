from src.core.command import command
from src.core.tools import fetch_json
from src.modules.message import RobotMessage

__hitokoto_version__ = "v1.0.2"


def register_module():
    pass


@command(tokens=["hitokoto", "来句", "来一句", "来句话", "来一句话"])
async def reply_hitokoto(message: RobotMessage):
    json = fetch_json("https://v1.hitokoto.cn/")
    content = json['hitokoto']
    where = json['from']
    author = json['from_who'] if json['from_who'] else ""
    await message.reply(f"[Hitokoto]\n{content}\nBy {author}「{where}」", modal_words=False)
