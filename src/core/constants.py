class Constants:
    CRON_PRIOR = 50
    PLATFORM_PRIOR = 100
    HELP_PRIOR = 1000
    MISC_PRIOR = 200
    core_version = "v3.1.0"
    bot_owner = 123456789
    SUPERUSERS=[f'{bot_owner}','...']
    help_contents = {
        'Codeforces': '\n'.join([
            "可用 /cf , /codeforces 触发",
            "/cf info [handle]: 获取用户名为 handle 的 Codeforces 基础用户信息.",
            "/cf recent [handle] (count): 获取用户名为 handle 的 Codeforces 最近 count 发提交，count 默认为 5.",
            "/cf pick [标签|all] (难度) (new): 从 Codeforces 上随机选题. 标签中间不能有空格，支持模糊匹配. 难度为整数或一个区间，格式为xxx-xxx"
            ". 末尾加上 new 参数则会忽视 P1000A 以前的题.",
            "/cf contests: 列出最近的 Codeforces 比赛.",
            "/cf tags: 用于列出 codeforces 平台的 tags (辅助 pick)."
        ]),
        'Atcoder': '\n'.join([
            "临时通知：目前 info 和 contests 功能受到 Atcoder 阻拦不可用。仅可以使用 pick 功能，已经向 Atcoder 发工单了。",
            "/atc info [handle]: 获取用户名为 handle 的 AtCoder 基础用户信息.",
            "/atc pick [比赛类型|all] (难度): 从 AtCoder 上随机选题，基于 Clist API"
            ". 比赛类型可选参数为 [abc, arc, agc, ahc, common, sp, all]"
            "，其中 common 涵盖前四个类型，而 sp 则是排除前四个类型. 难度为整数或一个区间，格式为xxx-xxx.",
            "/atc contests: 列出最近的 AtCoder 比赛."
        ]),
        'Nowcoder': '\n'.join([
            "/nk contests: 列出最近的 NowCoder 比赛.",
            "/nk info [uid]: 获取 id 为 uid 的牛客基础用户信息."
        ]),
        'cron / 定时模块': "\n".join([
            "/schedule add [platform] [contestId]: 将比赛 [contestId] 加入调用指令的私聊/群聊提醒列表中。",
        ]),
        'cron / 定时模块 (admin)': "\n".join([
            "/schedule addto [platform] [contestId] [boardcastTo]: 将比赛 [contestId] 加入[boardcastTo]群聊提醒列表中。",
            "/schedule all: 返回当前所有的 shedule 任务",
            "/schedule removeall 删除当前所有的固定时间提醒任务。"
        ]),
    }
    config = {
        'uptime_apikey':"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        'clist_apikey':"ApiKey username:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    }
    merged_help_content = ("[Functions]\n\n" +
                           "\n\n".join([f"[{module}]\n{helps}" for module, helps in help_contents.items() if not 'admin' in module]))
