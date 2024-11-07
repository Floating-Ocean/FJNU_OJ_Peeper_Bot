from utils.command import command
from utils.interact import RobotMessage
from utils.tools import _config, fetch_json

_api_key = _config["uptime_apikey"]


def fetch_status(check_url: str) -> int:
    data = fetch_json("https://api.uptimerobot.com/v2/getMonitors",
                      {"api_key": _api_key})

    if data["stat"] != "ok":
        return -1  # API 异常

    monitors = data["monitors"]
    for monitor in monitors:
        if monitor["url"] == check_url:
            return 1 if monitor["status"] == 2 else 0  # 1 活着, 0 似了

    return -1


@command()
async def alive(message: RobotMessage):
    status = [
        fetch_status("https://fjnuacm.top"),
        fetch_status("https://codeforces.com"),
        fetch_status("https://atcoder.jp")
    ]

    if min(status) == -1:
        await message.reply("[UptimeRobot Api] Api 异常")
        return

    info = "[UptimeRobot Api] "
    if min(status) == 1:
        info += "所有服务均正常\n"
    else:
        info += "部分服务存在异常\n"

    services = ["Fjnuacm OJ", "Codeforces", "Atcoder"]
    for i in range(3):
        status_text = "正常" if status[i] == 1 else "异常"
        info += f"\n[{services[i]}] {status_text}"

    await message.reply(info, modal_words=False)
