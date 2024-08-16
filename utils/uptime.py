import requests

from utils.interact import RobotMessage
from utils.tools import _config

_api_key = _config["uptime_apikey"]


def fetch_status(check_url: str) -> int:
    url = "https://api.uptimerobot.com/v2/getMonitors"
    payload = {"api_key": _api_key}
    response = requests.post(url, json=payload)

    if response.status_code != 200:
        raise ConnectionError(f"Filed to connect {check_url}, code {response.status_code}.")

    data = response.json()
    if data["stat"] != "ok":
        return -1  # API 异常

    monitors = data["monitors"]
    for monitor in monitors:
        if monitor["url"] == check_url:
            return 1 if monitor["status"] == 2 else 0  # 1 活着, 0 似了

    return -1


async def send_is_alive(message: RobotMessage):
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

    await message.reply(info)

