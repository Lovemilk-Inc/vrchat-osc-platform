# from __future__ import annotations  # fix loguru.Logger cannot import
import loguru
from requests import RequestException

from module_utils import import_module_from_url

__all__ = (
    'logger',
    'error_logger'
)

URL_PATH = 'Lovemilk-Inc/favourites/main/loguru/log.py'

GITHUB_PROXIES = {
    'https://raw.githubusercontent.com/',
    # GitHub CN proxies
    'https://mirror.ghproxy.com/https://raw.githubusercontent.com/',
    'https://github.jobcher.com/gh/https://raw.githubusercontent.com/',
    'https://raw.fgit.cf/',
}

for proxy in GITHUB_PROXIES:
    try:
        log = import_module_from_url('log', 'get', f'{proxy}{URL_PATH}', load2global=True)
        break
    except RequestException:
        pass
else:
    raise RuntimeError(f'could not import log.py from https://github.com/{URL_PATH}')

logger: "loguru.Logger" = log.logger
error_logger: "loguru.Logger" = log.error_logger
