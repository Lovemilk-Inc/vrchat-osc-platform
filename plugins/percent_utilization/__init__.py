import psutil
import gpustat

import sys
from datetime import datetime

from log import logger, error_logger
from client import VRChatClient, SpecialChars

from jstimer4py import set_interval

PER_CPU = False  # 将每个核心占用率加起来, 类似 *nix 显示方式

UPDATE_INTERVAL = 1  # 更新间隔, 秒, 最好不要低于 1

last_loop = datetime.now()


def loop(client: VRChatClient):
    global last_loop
    if (datetime.now() - last_loop).total_seconds() < UPDATE_INTERVAL:
        return
    last_loop = datetime.now()

    if PER_CPU:
        cpu_usage = sum(psutil.cpu_percent(interval=UPDATE_INTERVAL, percpu=True))
    else:
        cpu_usage = psutil.cpu_percent(interval=UPDATE_INTERVAL, percpu=False)

    memory = psutil.virtual_memory()
    memory_usage = memory.percent

    swap = psutil.swap_memory()
    swap_usage = swap.percent

    gpu_stats = list(gpustat.GPUStatCollection.new_query())
    gpu0 = gpu_stats[0]

    logger.trace('flush status')

    client.chat(
        f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
        # Can't get real CPU usage for Micro$oft Windows!!!
        f'CPU: {round(cpu_usage, 2)}%{f" / {psutil.cpu_count() * 100}%" if PER_CPU else ""} '  # FUCK M$ WINDOWS
        f'GPU: {gpu0.utilization}%\n'
        f'RAM: {round(memory.used / (1024 ** 3), 2)}GiB / {round(memory.total / (1024 ** 3), 2)}GiB '
        f'{round(memory_usage, 2)}%\n'
        f'SWAP: {round(swap.used / (1024 ** 3), 2)}GiB / {round(swap.total / (1024 ** 3), 2)}GiB '
        f'{round(swap_usage, 2)}%\n'
        f'GRAM: {round(gpu0.memory_used / (1024 ** 1), 2)}GiB / '
        f'{round(gpu0.memory_total / (1024 ** 1), 2)}GiB '
        f'{round((gpu0.memory_used / gpu0.memory_total) * 100, 2)}%\n'
        .replace('\n', SpecialChars.RETURN)
    )


def apply():
    if sys.platform == 'win32':
        logger.warning(
            'CPU usage is different between Windows taskmgr and this process gotten (both PER_CPU is true or false) '
            'on Windows operating system'
            # 'FUCK M$ WINDOWS'
        )
    set_interval(loop, 3)
