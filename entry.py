import base64
import importlib
import os

import nest_asyncio
import psutil
import urllib3

from robot import open_robot_session

nest_asyncio.apply()
urllib3.disable_warnings()

# 加载模块
importlib.import_module("src.modules")


if __name__ == '__main__':
    # a lock containing pid
    if os.path.exists('robot.py.lock'):
        with open('robot.py.lock', 'rb') as lock_file:
            old_pid = int(base64.b85decode(lock_file.read()).decode())
            if psutil.pid_exists(old_pid):
                psutil.Process().kill()

    with open('robot.py.lock', 'wb') as lock_file:
        lock_file.write(base64.b85encode(str(os.getpid()).encode()))

    open_robot_session()

    os.remove('robot.py.lock')
