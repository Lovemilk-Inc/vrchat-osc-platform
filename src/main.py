import sys
import time
import inspect
from pathlib import Path
from pythonosc import udp_client
from importlib import import_module
from threading import Timer

from log import logger, error_logger
from client import VRChatClient
from hmr import hmr

PLUGINS_PATH = Path('./plugins/')
HOST = '127.0.0.1'
PORT = 9000
LOOP_INTERVAL = 0.5

sys.path.append('.')


def loop_module(module, vrchat_client: VRChatClient):
    if not callable(getattr(module, 'loop', None)):
        return

    loop = module.loop
    params_length = len(inspect.signature(loop).parameters)

    # match params_length:

    Timer(0, lambda: loop(vrchat_client)).start()


def apply_module(module, vrchat_client: VRChatClient, host: str, port: int):
    if not callable(getattr(module, 'apply', None)):
        return

    func = module.apply
    params_length = len(inspect.signature(func).parameters)

    def _apply():
        # noinspection PyBroadException
        try:
            match params_length:
                case 0:
                    func()
                case 1:
                    func(vrchat_client)
                case 2:
                    func(vrchat_client, (host, port))
                case 3:
                    func(vrchat_client, host, port)
                case _:
                    func(vrchat_client, host, port, *[None for _ in range(params_length - 3)])

            logger.success(f'apply {module.__name__}')
        except Exception:
            error_logger.warning(f'failed to apply module: {module.__name__}')

    Timer(0, _apply).start()  # not blocking


def main(host: str, port: int):
    logger.debug('start to connect to VRChat\'s OSC')
    client = udp_client.SimpleUDPClient(host, port)
    vrchat_client = VRChatClient(client)
    logger.debug('connected to VRChat\'s OSC')

    plugins = []
    for plugin_dir in PLUGINS_PATH.iterdir():
        if not plugin_dir.is_dir():
            continue

        if not (plugin_dir / '__init__.py').is_file():
            continue

        module_name = f'plugins.{plugin_dir.name}'
        logger.debug(f'start to load plugin: {module_name}')
        module = import_module(module_name)
        logger.debug(f'loaded, start to apply {module_name}')

        apply_module(module, vrchat_client, host, port)

        # Watchdog is not supported for Micro$oft Windows!!!
        if sys.platform != 'win32':  # FUCK M$ WINDOWS
            module = hmr(module, lambda _, reloaded_module: (
                apply_module(reloaded_module, vrchat_client, host, port),
                logger.debug(f'hmr reload: {reloaded_module.__name__}')
            ))

        plugins.append(module)

    try:
        while True:
            start = time.time()
            for module in plugins:
                loop_module(module, vrchat_client)

            sleep_time = LOOP_INTERVAL - (time.time() - start)
            if sleep_time <= 0:
                continue

            time.sleep(sleep_time)
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main(HOST, PORT)
