import base64
import importlib
import os.path
import signal

import nest_asyncio
import urllib3

from robot import open_robot_session

nest_asyncio.apply()
urllib3.disable_warnings()

# 加载模块
importlib.import_module("src.modules")


def terminate_process(pid: int):
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass


if __name__ == '__main__':
    # a lock containing pid
    if os.path.exists('robot.py.lock'):
        with open('robot.py.lock', 'rb') as lock_file:
            terminate_process(int(base64.b85decode(lock_file.read()).decode()))

    with open('robot.py.lock', 'wb') as lock_file:
        lock_file.write(base64.b85encode(str(os.getpid()).encode()))

    open_robot_session()

    os.remove('robot.py.lock')
