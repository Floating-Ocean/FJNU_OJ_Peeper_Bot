import difflib
import json
import os
import random

import traceback

from utils.interact import RobotMessage
from utils.tools import _config, report_exception, save_img, _log

_lib_path = _config["lib_path"] + "\\Pick-One"
__pick_one_version__ = "v2.2.4"

__pick_one_help_content__ = """/来只 [what]: 获取一个类别为 what 的随机表情包.
/随便来只: 获取一个随机类别的随机表情包."""

_lib_config, _match_dict, _ids = {}, {}, []


def load_pick_one_config():
    with open(_lib_path + "\\config.json", 'r', encoding="utf-8") as f:
        _lib_config.clear(), _ids.clear(), _match_dict.clear()
        _lib_config.update(json.load(f))
        for key, value in _lib_config.items():  # 方便匹配
            _ids.append([value['_id'], len(os.listdir(f"{_lib_path}\\{key}\\"))])
            for keys in value['key']:
                _match_dict[keys] = key
        _ids.sort(key=lambda s: s[1], reverse=True)  # 按图片数量降序排序


async def reply_pick_one(message: RobotMessage, what: str, add: bool = False):
    load_pick_one_config()
    try:
        if add:
            await save_one(message, what)
        else:
            await pick_one(message, what)
    except Exception as e:
        await report_exception(message, 'Pick-One', traceback.format_exc(), repr(e))


async def pick_one(message: RobotMessage, what: str):
    if what.lower() == "random" or what.lower() == "rand" or what.lower() == "随机" or what.lower() == "随便":
        current_key = random.choice(list(_lib_config.keys()))
    elif what.lower() in _match_dict.keys():
        current_key = _match_dict[what.lower()]
    else:  # 支持一下模糊匹配
        matches = difflib.get_close_matches(what.lower(), _match_dict.keys())
        if len(matches) == 0:
            img_help = "目前可以来只:\n\n"
            img_help += ", ".join([_id for _id, _len in _ids])
            await message.reply(img_help, modal_words=False)
            return
        current_key = _match_dict[matches[0]]

    current_config = _lib_config[current_key]
    dir_path = f"{_lib_path}\\{current_key}\\"
    img_len = len(os.listdir(dir_path))

    if img_len == 0:
        await message.reply(f"这里还没有 {current_config['_id']} 的图片")
    else:
        rnd_idx = random.randint(1, img_len) + random.randint(1, img_len) + random.randint(1, img_len)
        rnd_idx = (rnd_idx - 1) % img_len + 1
        await message.reply(f"来了一只{current_config['_id']}",
                            img_path=f"{dir_path}{current_config['_id']}_{rnd_idx}.gif")


async def save_one(message: RobotMessage, what: str):
    _log.info(f"{message.author_id} attempted to add new img.")
    if message.author_id not in _config['admin_qq_id'] and message.author_id not in _config['mod_qq_id']:
        await message.reply("添加失败，只有bot管理员才能添加")
        return

    if what.lower() in _match_dict.keys():
        current_key = _match_dict[what.lower()]
        current_config = _lib_config[current_key]
        dir_path = f"{_lib_path}\\{current_key}\\"
        img_len = len(os.listdir(dir_path))
        cnt, ok = len(message.attachments), 0

        for attach in message.attachments:
            if not attach.__dict__['content_type'].startswith('image'):
                continue  # 不是图片
            file_path = f"{dir_path}{current_config['_id']}_{img_len + 1}.gif"
            response = await save_img(attach.__dict__['url'], file_path)
            if response:
                ok += 1
                img_len += 1

        if cnt == 0:
            await message.reply(f"未识别到图片，请将图片和指令发送在同一条消息中")
        else:
            failed_info = "" if cnt == ok else f"，失败 {cnt - ok} 张"
            await message.reply(f"已添加 {ok} 张图片至 {current_key} 中{failed_info}")

    else:
        img_help = f"关键词 {what} 未被记录，请联系bot管理员添加" if len(what) > 0 else "请指定需要添加的图片的关键词"
        await message.reply(img_help)
