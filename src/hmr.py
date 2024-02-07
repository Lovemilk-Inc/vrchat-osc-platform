import atexit
import importlib
from log import logger, error_logger
from pathlib import Path
from typing import Callable, Any
from types import ModuleType

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

CallbackType = Callable[[FileModifiedEvent, ModuleType], Any]


class HMRHandler(FileSystemEventHandler):
    def __init__(self, module, hmr_obj, callback: CallbackType):
        super().__init__()
        self.module = module
        self.hmr_obj = hmr_obj

        self.callback = callback

    def on_modified(self, event: FileModifiedEvent):
        try:
            self.module = self.hmr_obj.__module__ = importlib.reload(self.module)
        except ImportError:
            error_logger.warning(f'hmr failed to load module: {self.module.__name__}')
            return

        self.callback(event, self.module)


def hmr(module: ModuleType, callback: CallbackType):
    module_file = str(Path(module.__file__))
    logger.debug(f'hmr add: {module}: {module_file}')

    observer = Observer()

    hmr_obj = type('HMRObject', (), {
        "__module__": module,
        "__getattribute__": lambda self, p: getattr(type(self).__module__, p)
    })

    observer.schedule(HMRHandler(module, hmr_obj, callback), module_file)
    observer.start()
    atexit.register(observer.stop)
    return hmr_obj()
