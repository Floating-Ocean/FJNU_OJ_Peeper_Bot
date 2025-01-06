import base64
import os
import subprocess

import psutil
from apscheduler.schedulers.blocking import BlockingScheduler

from src.core.constants import Constants

daemon_scheduler = BlockingScheduler()


def open_entry():
    subprocess.Popen("pythonw entry.py")


def check_process_job():
    if os.path.exists("robot.py.lock"):
        with open("robot.py.lock", "rb") as lock_file:
            pid = int(base64.b85decode(lock_file.read()).decode())
            if psutil.pid_exists(pid):
                # Constants.log.debug(f"[daemon] lock pid: {pid}, running")
                return

    Constants.log.info("[daemon] 进程不存在，正在创建")
    open_entry()
    Constants.log.info("[daemon] 进程创建完成")


if __name__ == '__main__':
    try:
        Constants.log.info("[daemon] 守护进程开始运行")
        check_process_job()  # scheduler开始运行前也会等待interval，所以先运行一下
        daemon_scheduler.add_job(check_process_job, "interval", minutes=1)
        daemon_scheduler.start()

    except (KeyboardInterrupt, SystemExit):
        Constants.log.info("[daemon] 守护进程开始终止")
        pass
