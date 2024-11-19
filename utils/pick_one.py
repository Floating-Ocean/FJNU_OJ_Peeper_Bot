import difflib
import json
import os
import random

from utils.command import command
from utils.interact import RobotMessage
from utils.tools import _config, save_img, rand_str_len32, get_md5

_lib_path = _config["lib_path"] + "\\Pick-One"
__pick_one_version__ = "v2.3.1"

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


_what_dict = {
    '随机来只': 'rand',
    '随便来只': 'rand',
    'capoo': 'capoo',
    '咖波': 'capoo',
}


@command(aliases=["来只*"] + list(_what_dict.keys()))
async def pick_one(message: RobotMessage):
    func = message.pure_content[0][1:]
    what = _what_dict[func] if func in _what_dict else (
        message.pure_content[1].lower() if len(message.pure_content) > 2 else "")
    if what == "rand" or what == "随便" or what == "随机":
        current_key = random.choice(list(_lib_config.keys()))
    elif what in _match_dict.keys():
        current_key = _match_dict[what]
    else:  # 支持一下模糊匹配
        matches = difflib.get_close_matches(what, _match_dict.keys())
        if len(matches) == 0:
            img_help = "目前可以来只:\n\n"
            img_help += ", ".join([_id for _id, _len in _ids])
            await message.reply(img_help, modal_words=False)
            return
        current_key = _match_dict[matches[0]]

    current_config = _lib_config[current_key]
    dir_path = f"{_lib_path}\\{current_key}\\"
    img_list = os.listdir(dir_path)
    img_len = len(img_list)

    if img_len == 0:
        await message.reply(f"这里还没有 {current_config['_id']} 的图片")
    else:
        rnd_idx = random.randint(1, img_len) + random.randint(1, img_len) + random.randint(1, img_len)
        rnd_idx = (rnd_idx - 1) % img_len
        await message.reply(f"来了一只{current_config['_id']}",
                            img_path=f"{dir_path}{img_list[rnd_idx]}")


@command(aliases=["添加来只*", "添加*"])
async def save_one(message: RobotMessage):
    if len(message.pure_content) < 2:
        await message.reply("请指定需要添加的图片的关键词")
        return

    audit = message.user_permission_level == 0
    what = message.pure_content[1].lower()

    if what in _match_dict.keys():
        current_key = _match_dict[what]
        audit_prefix = "\\__AUDIT__" if audit else ""
        dir_path = f"{_lib_path}{audit_prefix}\\{current_key}\\"
        real_dir_path = f"{_lib_path}\\{current_key}\\"
        cnt, ok, duplicate = len(message.attachments), 0, 0

        for attach in message.attachments:
            if not attach.__dict__['content_type'].startswith('image'):
                continue  # 不是图片

            file_path = f"{dir_path}{rand_str_len32()}.gif"
            response = await save_img(attach.__dict__['url'], file_path)

            if response:
                md5 = get_md5(file_path)

                if os.path.exists(f"{real_dir_path}{md5}.gif") or os.path.exists(f"{dir_path}{md5}.gif"):
                    os.remove(file_path)
                    duplicate += 1  # 图片重复
                    continue

                os.rename(file_path, f"{dir_path}{md5}.gif")
                ok += 1

        if cnt == 0:
            await message.reply(f"未识别到图片，请将图片和指令发送在同一条消息中")
        else:
            failed_info = ""
            if duplicate > 0:
                failed_info += f"，重复 {duplicate} 张"
            if cnt - ok - duplicate > 0:
                failed_info += f"，失败 {cnt - ok - duplicate} 张"

            audit_suffix = "审核队列" if audit else ""
            main_info = "非Bot管理员添加的图片需要审核。\n" if audit else ""
            main_info += f"已添加 {ok} 张图片至 {current_key} {audit_suffix}中" if ok > 0 else "没有图片被添加"
            await message.reply(f"{main_info}{failed_info}")

    else:
        img_help = f"关键词 {what} 未被记录，请联系bot管理员添加" if len(what) > 0 else "请指定需要添加的图片的关键词"
        await message.reply(img_help)


@command(aliases=["审核来只", "同意来只", "accept", "audit"], permission_level=1)
async def audit_accept(message: RobotMessage):
    dir_path = f"{_lib_path}\\"
    audit_dir_path = f"{dir_path}__AUDIT__\\"
    tags = [tag for tag in os.listdir(audit_dir_path)
            if os.path.isdir(os.path.join(audit_dir_path, tag))]  # 遍历文件夹
    cnt, ok = 0, 0
    ok_dict: dict[str, int] = {}

    for tag in tags:
        if not os.path.exists(os.path.join(dir_path, tag)):
            continue

        img_list = [img for img in os.listdir(os.path.join(audit_dir_path, tag))
                    if os.path.isfile(os.path.join(audit_dir_path, tag, img))]

        for img in img_list:
            cnt += 1
            if os.path.exists(os.path.join(dir_path, tag, img)):
                continue  # 图片重复
            os.rename(os.path.join(audit_dir_path, tag, img), os.path.join(dir_path, tag, img))
            ok += 1
            ok_dict[tag] = ok_dict.get(tag, 0) + 1

    if cnt == 0:
        await message.reply(f"没有需要审核的图片")
    else:
        failed_info = ""
        if cnt - ok > 0:
            failed_info += f"，失败 {cnt - ok} 张"

        audit_detail = '\n'.join([f"[{tag}] {ok_count} 张" for tag, ok_count in ok_dict.items()])
        info = f"已审核 {ok} 张图片{failed_info}\n\n{audit_detail}" if ok > 0 else f"没有图片被添加{failed_info}"
        await message.reply(info, modal_words=False)
