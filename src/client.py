from pythonosc.udp_client import SimpleUDPClient
from time import sleep
from enum import StrEnum

from jstimer4py import set_timeout

__all__ = (
    'VRChatClient',
    'SpecialChars'
)


class SpecialChars(StrEnum):
    RETURN = '\v'


class VRChatClient:
    def __init__(self, client: SimpleUDPClient):
        self.client = client

    def send_message(self, path: str, value: str | bytes | bool | int | float | tuple[int, int, int, int] | list):
        """
        send any message to OSC server
        :param path: path to endpoint
        :param value: content in any supported type
        :return: None
        """
        self.client.send_message(path, value)

    def chat(self, message: str, send_message: bool = True, notification_sfx: bool = True):
        """
        send str message to chat box
        :param message: the content of the message
        :param send_message: send message immediately or not
        :param notification_sfx: is an additional bool parameter that when set to False will not trigger the
        notification SFX (defaults to True if not specified)
        (Copied from https://docs.vrchat.com/docs/osc-as-input-controller#supported-inputs)
        :return: None
        """
        # noinspection SpellCheckingInspection
        self.client.send_message('/chatbox/input', [message, send_message, notification_sfx])

    def jump(self, release_interval: float = 0.05):
        """
        jump once
        :param release_interval: release the jump button delay (seconds), the function will block until released
        :return: None
        """
        self.client.send_message('/input/Jump', 1)
        sleep(release_interval)
        self.client.send_message('/input/Jump', 0)

    def jump_noblock(self, release_interval: float = 0.05):
        """
        jump once but not wait for the releasing block
        :param release_interval: release the jump button delay (seconds), the function will finish immediately
        :return: None
        """
        self.client.send_message('/input/Jump', 1)
        set_timeout(lambda: self.client.send_message('/input/Jump', 0), release_interval)
