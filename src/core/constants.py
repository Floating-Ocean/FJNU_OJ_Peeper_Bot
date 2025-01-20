import os

from botpy import logging
from botpy.ext.cog_yaml import read


class Constants:
    log = logging.get_logger()
    config = read(os.path.join(os.path.dirname(__file__), "..", "..", "config.yaml"))

    core_version = "v3.0.4"

    key_words = [
        [["傻逼"], ["谢谢夸奖", "反弹", "可能还真被你说对了", "嗯", "好的", "哼，你才是",
                  "哈哈", "你可能说对了，你可能没说对", "干什么"]],
        [["性别"], ["盲猜我的性别是武装直升机", "我也不知道我的性别是啥"]],
        [["干嘛", "干什么"], ["how", "what", "which", "why", "whether", "when"]],
        [["谢谢", "thank"], ["qaq", "不用谢qaq", "qwq"]],
        [["qaq", "qwq"], ["qwq"]],
        [["你是谁", "你谁"], ["猜猜我是谁", "我也不知道", "你是谁"]],
        [["省"], ["妈妈生的", "一眼丁真"]],
        [["似"], ["看上去我还活着", "似了"]],
        [["go"], ["哎你们这些go批", "还在go还在go"]],
        [["春日影"], ["为什么要演奏春日影"]],
        [["乌蒙"], ["哎你们这些wmc", "awmc", "我们乌蒙怎么你了"]]
    ]

    modal_words = ["喵", "呢", "捏", "qaq"]

    pick_one_help_content = f"""/来只 [what]: 获取一个类别为 what 的随机表情包.
/随便来只: 获取一个随机类别的随机表情包.
/添加(来只) [what]: 添加一个类别为 what 的表情包，需要管理员审核."""

    cf_help_content = f"""/cf info [handle]: 获取用户名为 handle 的 Codeforces 基础用户信息.
/cf recent [handle] (count): 获取用户名为 handle 的 Codeforces 最近 count 发提交，count 默认为 5.
/cf pick [标签|all] (难度) (New): 从 Codeforces 上随机选题. 标签中间不能有空格，支持模糊匹配. 难度为整数或一个区间，格式为xxx-xxx. 末尾加上 New 参数则会忽视 P1000A 以前的题.
/cf contest: 列出最近的 Codeforces 比赛.
/cf tag: 列出 Codeforces 上的所有题目标签."""

    atc_help_content = f"""/atc info [handle]: 获取用户名为 handle 的 AtCoder 基础用户信息.
/atc contest: 列出最近的 AtCoder 比赛."""

    nk_help_content = f"""/nk contest: 列出最近的 NowCoder 比赛."""

    rand_help_content = f"""/rand [num/int] [min] [max]: 在 [min, max] 中选择一个随机数，值域 [-1e9, 1e9].
/rand seq [max]: 获取一个 1, 2, ..., max 的随机排列，值域 [1, 500]."""

    hitokoto_help_content = f"""/hitokoto: 获取一条一言。指令别名：/一言，/来(一)句(话)"""

    color_rand_help_content = f"""/color: 获取一个色卡。"""

    help_content = f"""[Functions]

[Main]
/今日题数: 查询今天从凌晨到现在的做题数情况.
/昨日总榜: 查询昨日的完整榜单.
/评测榜单 [verdict]: 查询分类型榜单，其中指定评测结果为第二参数 verdict，需要保证参数中无空格，如 wa, TimeExceeded.

[sub]
/user id [uid]: 查询 uid 对应用户的信息.
/user name [name]: 查询名为 name 对应用户的信息，支持模糊匹配.
/contests (platform): 查询 platform 平台近日比赛，可指定 Codeforces, AtCoder, NowCoder，留空则返回三平台近日比赛集合.
/alive: 检查 OJ, Codeforces, AtCoder 的可连通性.
/api: 获取当前各模块的构建信息.

[robot]
/活着吗: 顾名思义，只要活着回你一句话，不然就不理你. 等效命令为 /ping.

[pick-one]
{pick_one_help_content}

[codeforces]
{cf_help_content}

[atcoder]
{atc_help_content}

[nowcoder]
{nk_help_content}

[random]
{rand_help_content}

[hitokoto]
{hitokoto_help_content}

[color-rand]
{color_rand_help_content}

[misc]
/qrcode [content]：生成一个内容为 content 的二维码."""
