import random

_key_words = {
    "傻逼": "谢谢夸奖",
    "性别": "盲猜我的性别是武装直升机",
    "干嘛": "how",
    "谢谢": "qaq",
    "qaq": "qwq",
    "你是谁": "猜猜我是谁",
    "愚蠢": "yes，我只会关键词匹配",
    "龟": "乌龟是什么，我只知道杰尼龟",
}
_capoo_list_len = 456


def match_key_words(content):
    for each in _key_words:
        if each in content:
            return _key_words[each]
    return "你干嘛"


async def reply(me, message, content, img_path=None):
    await me.api.post_message(channel_id=message.channel_id, msg_id=message.id,
                                content=f"<@{message.author.id}>{content}", file_image=img_path)


async def reply_directly(me, channel_id, content, img_path=None):
    await me.api.post_message(channel_id=channel_id, content=f"{content}", file_image=img_path)


async def reply_capoo(me, message):
    await me.api.post_message(channel_id=message.channel_id, msg_id=message.id,
                                content=f"<@{message.author.id}>[capoo]",
                                image=f"https://git.acwing.com/HuParry/capoo/-/raw/master/capoo ({random.randint(1, _capoo_list_len)}).gif")
