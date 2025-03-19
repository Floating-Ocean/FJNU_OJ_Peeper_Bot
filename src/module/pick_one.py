import difflib
import json
import os
import random

from src.core.command import command, PermissionLevel
from src.core.constants import Constants
from src.core.tools import save_img, rand_str_len32, get_md5
from src.module.message import RobotMessage

_lib_path = os.path.join(Constants.config["lib_path"], "Pick-One")
__pick_one_version__ = "v2.3.1"

_lib_config, _match_dict, _ids = {}, {}, []


def register_module():
    pass


def load_pick_one_config():
    with open(os.path.join(_lib_path, "config.json"), 'r', encoding="utf-8") as f:
        _lib_config.clear(), _ids.clear(), _match_dict.clear()
        _lib_config.update(json.load(f))
        for key, value in _lib_config.items():  # 方便匹配
            _ids.append([value['_id'], len(os.listdir(os.path.join(_lib_path, key)))])
            for keys in value['key']:
                _match_dict[keys] = key
        _ids.sort(key=lambda s: s[1], reverse=True)  # 按图片数量降序排序


_what_dict = {
    '随机来只': 'rand',
    '随便来只': 'rand',
    'capoo': 'capoo',
    '咖波': 'capoo',
}


@command(tokens=["来只*"] + list(_what_dict.keys()))
def pick_one(message: RobotMessage):
    load_pick_one_config()

    func = message.tokens[0][1:]
    what = _what_dict[func] if func in _what_dict else (
        message.tokens[1].lower() if len(message.tokens) >= 2 else "")
    if what == "rand" or what == "随便" or what == "随机":
        current_key = random.choice(list(_lib_config.keys()))
    elif what in _match_dict.keys():
        current_key = _match_dict[what]
    else:  # 支持一下模糊匹配
        matches = difflib.get_close_matches(what, _match_dict.keys())
        if len(matches) == 0:
            img_help = "目前可以来只:\n\n"
            img_help += ", ".join([_id for _id, _len in _ids])
            message.reply(img_help, modal_words=False)
            return
        current_key = _match_dict[matches[0]]

    current_config = _lib_config[current_key]
    dir_path = os.path.join(_lib_path, current_key)
    img_list = os.listdir(dir_path)
    img_len = len(img_list)

    if img_len == 0:
        message.reply(f"这里还没有 {current_config['_id']} 的图片")
    else:
        rnd_idx = random.randint(1, img_len) + random.randint(1, img_len) + random.randint(1, img_len)
        rnd_idx = (rnd_idx - 1) % img_len
        message.reply(f"来了一只{current_config['_id']}",
                            img_path=f"{dir_path}{img_list[rnd_idx]}")


@command(tokens=["添加来只*", "添加*"])
def save_one(message: RobotMessage):
    load_pick_one_config()

    if len(message.tokens) < 2:
        message.reply("请指定需要添加的图片的关键词")
        return

    audit = message.user_permission_level == 0
    what = message.tokens[1].lower()

    if what in _match_dict.keys():
        current_key = _match_dict[what]
        dir_path = (os.path.join(_lib_path, "__AUDIT__", current_key) if audit else
                    os.path.join(_lib_path, current_key))
        real_dir_path = os.path.join(_lib_path, current_key)
        cnt, ok, duplicate = len(message.attachments), 0, 0

        for attach in message.attachments:
            if not attach.__dict__['content_type'].startswith('image'):
                continue  # 不是图片

            file_path = f"{dir_path}{rand_str_len32()}.gif"
            response = save_img(attach.__dict__['url'], file_path)

            if response:
                md5 = get_md5(file_path)

                if os.path.exists(f"{real_dir_path}{md5}.gif") or os.path.exists(f"{dir_path}{md5}.gif"):
                    os.remove(file_path)
                    duplicate += 1  # 图片重复
                    continue

                os.rename(file_path, f"{dir_path}{md5}.gif")
                ok += 1

        if cnt == 0:
            message.reply(f"未识别到图片，请将图片和指令发送在同一条消息中")
        else:
            failed_info = ""
            if duplicate > 0:
                failed_info += f"，重复 {duplicate} 张"
            if cnt - ok - duplicate > 0:
                failed_info += f"，失败 {cnt - ok - duplicate} 张"

            audit_suffix = "审核队列" if audit else ""
            main_info = "非Bot管理员添加的图片需要审核。\n" if audit else ""
            main_info += f"已添加 {ok} 张图片至 {current_key} {audit_suffix}中" if ok > 0 else "没有图片被添加"
            message.reply(f"{main_info}{failed_info}")

    else:
        img_help = f"关键词 {what} 未被记录，请联系bot管理员添加" if len(what) > 0 else "请指定需要添加的图片的关键词"
        message.reply(img_help)


@command(tokens=["审核来只", "同意来只", "accept", "audit"], permission_level=PermissionLevel.MOD)
def audit_accept(message: RobotMessage):
    load_pick_one_config()

    audit_dir_path = os.path.join(_lib_path, "__AUDIT__")
    tags = [tag for tag in os.listdir(audit_dir_path)
            if os.path.isdir(os.path.join(audit_dir_path, tag))]  # 遍历文件夹
    cnt, ok = 0, 0
    ok_dict: dict[str, int] = {}

    for tag in tags:
        if not os.path.exists(os.path.join(_lib_path, tag)):
            continue

        img_list = [img for img in os.listdir(os.path.join(audit_dir_path, tag))
                    if os.path.isfile(os.path.join(audit_dir_path, tag, img))]

        for img in img_list:
            cnt += 1
            if os.path.exists(os.path.join(_lib_path, tag, img)):
                continue  # 图片重复
            os.rename(os.path.join(audit_dir_path, tag, img), os.path.join(_lib_path, tag, img))
            ok += 1
            ok_dict[tag] = ok_dict.get(tag, 0) + 1

    if cnt == 0:
        message.reply(f"没有需要审核的图片")
    else:
        failed_info = ""
        if cnt - ok > 0:
            failed_info += f"，失败 {cnt - ok} 张"

        audit_detail = '\n'.join([f"[{tag}] {ok_count} 张" for tag, ok_count in ok_dict.items()])
        info = f"已审核 {ok} 张图片{failed_info}\n\n{audit_detail}" if ok > 0 else f"没有图片被添加{failed_info}"
        message.reply(info, modal_words=False)
