import json
import os
import random
import traceback

from utils.interact import RobotMessage
from utils.tools import _config, report_exception

_lib_path = _config["lib_path"] + "\\Pick-One"
__pick_one_version__ = "v2.1.1"

with open(_lib_path + "\\config.json", 'r', encoding="utf-8") as f:
    _lib_config: dict = json.load(f)
    _match_dict, _ids = {}, []
    for key, value in _lib_config.items():  # 方便匹配
        _ids.append(value['_id'])
        for keys in value['key']:
            _match_dict[keys] = key


async def reply_pick_one(message: RobotMessage, what: str):
    try:
        if what.lower() in _match_dict.keys():
            current_key = _match_dict[what.lower()]
            current_config = _lib_config[current_key]
            dir_path = _lib_path + f"\\{current_key}\\"
            img_len = len(os.listdir(dir_path))
            rnd_idx = random.randint(1, img_len) + random.randint(1, img_len) + random.randint(1, img_len)
            rnd_idx = (rnd_idx - 1) % img_len + 1
            await message.reply(f"[来只 {current_config['_id']}]",
                                img_path=f"{dir_path}{current_config['_id']}_{rnd_idx}.gif")
        else:
            img_help = "目前可以来只:\n\n"
            img_help += ", ".join(_ids)
            await message.reply(img_help)

    except Exception as e:
        await report_exception(message, 'Pick-One', traceback.format_exc())
