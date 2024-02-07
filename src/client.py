from pythonosc.udp_client import SimpleUDPClient
from time import sleep
from enum import StrEnum

from settimeout import set_timeout

__all__ = (
    'VRChatClient',
    'SpecialChars'
)


class SpecialChars(StrEnum):
    RETURN = '\v'


class VRChatClient:
    def __init__(self, client: SimpleUDPClient):
        self.client = client

    def chat(self, message: str, send_message: bool = True, notification_sfx: bool = True):
        # noinspection SpellCheckingInspection
        self.client.send_message('/chatbox/input', [message, send_message, notification_sfx])

    def jump(self, release_interval: float = 0.05):
        self.client.send_message('/input/Jump', 1)
        sleep(release_interval)
        self.client.send_message('/input/Jump', 0)

    def jump_noblock(self, release_interval: float = 0.05):
        self.client.send_message('/input/Jump', 1)
        set_timeout(lambda: self.client.send_message('/input/Jump', 0), release_interval)
