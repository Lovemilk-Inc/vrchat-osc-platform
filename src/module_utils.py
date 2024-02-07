import sys
import requests
from types import ModuleType


def import_module_from_string(
        global_name: str, exec_string: str, *, load2global: bool = False, desc: str = ''
) -> ModuleType:
    module = ModuleType(global_name, desc)
    exec(exec_string, module.__dict__)

    if load2global:
        sys.modules[global_name] = module

    return module


def import_module_from_url(
        global_name: str, method: str, url: str, *, headers=None, load2global: bool = False, desc: str = ''
) -> ModuleType:
    # noinspection SpellCheckingInspection
    headers = headers or {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'
    }

    response = requests.request(method.upper(), url, headers=headers)
    exec_string = response.text

    return import_module_from_string(global_name, exec_string, load2global=load2global, desc=desc)


if __name__ == '__main__':
    print(import_module_from_url(
        'test',
        'get',
        'https://raw.githubusercontent.com/Lovemilk-Inc/favourites/main/loguru/log.py',
    ))
