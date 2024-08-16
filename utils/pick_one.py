import json
import os
import random
import traceback

from utils.interact import RobotMessage
from utils.tools import _config, report_exception, save_img, _log

_lib_path = _config["lib_path"] + "\\Pick-One"
__pick_one_version__ = "v2.1.2"

with open(_lib_path + "\\config.json", 'r', encoding="utf-8") as f:
    _lib_config: dict = json.load(f)
    _match_dict, _ids = {}, []
    for key, value in _lib_config.items():  # 方便匹配
        _ids.append(value['_id'])
        for keys in value['key']:
            _match_dict[keys] = key


async def reply_pick_one(message: RobotMessage, what: str, add: bool = False):
    try:
        if add:
            await save_one(message, what)
        else:
            await pick_one(message, what)
    except Exception as e:
        await report_exception(message, 'Pick-One', traceback.format_exc())


async def pick_one(message: RobotMessage, what: str):
    if what.lower() in _match_dict.keys():
        current_key = _match_dict[what.lower()]
        current_config = _lib_config[current_key]
        dir_path = _lib_path + f"\\{current_key}\\"
        img_len = len(os.listdir(dir_path))

        if img_len == 0:
            await message.reply(f"[来只 {current_config['_id']}] 这里还没有图片呢")
        else:
            rnd_idx = random.randint(1, img_len) + random.randint(1, img_len) + random.randint(1, img_len)
            rnd_idx = (rnd_idx - 1) % img_len + 1
            await message.reply(f"[来只 {current_config['_id']}]",
                                img_path=f"{dir_path}{current_config['_id']}_{rnd_idx}.gif")
    else:
        img_help = "目前可以来只:\n\n"
        img_help += ", ".join(_ids)
        await message.reply(img_help)


async def save_one(message: RobotMessage, what: str):
    _log.info(f"{message.author_id} attempted to add new img.")
    if message.author_id not in _config['admin_qq_id'] and message.author_id not in _config['mod_qq_id']:
        await message.reply("添加失败，只有bot管理员才能添加")

    if what.lower() in _match_dict.keys():
        current_key = _match_dict[what.lower()]
        current_config = _lib_config[current_key]
        dir_path = _lib_path + f"\\{current_key}\\"
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
