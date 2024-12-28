import base64
import os
import subprocess

from apscheduler.schedulers.blocking import BlockingScheduler

from src.core.constants import Constants

daemon_scheduler = BlockingScheduler()


def open_entry():
    subprocess.Popen("pythonw entry.py")


def check_process_with_pid(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def check_process_job():
    if os.path.exists("robot.py.lock"):
        with open("robot.py.lock", "rb") as lock_file:
            pid = int(base64.b85decode(lock_file.read()).decode())
            if check_process_with_pid(pid):
                return

    Constants.daemon_log.info("[Daemon] 进程不存在，正在创建")
    open_entry()
    Constants.daemon_log.info("[Daemon] 进程创建完成")


if __name__ == '__main__':
    try:
        daemon_scheduler.add_job(check_process_job, "interval", minutes=2)
        daemon_scheduler.start()

        Constants.daemon_log.info("[Daemon] 守护进程开始运行")
    except (KeyboardInterrupt, SystemExit):
        Constants.daemon_log.info("[Daemon] 守护进程开始终止")
        pass
