import logging
import os.path
import threading
from typing import List, Union, Generator, Dict

from utils import ReadWriteLock


class PeerNode:
    def __init__(self, name: str = '', ip: str = '', port: int = -1, online: bool = True):
        self.name = name
        self.ip = ip
        self.port = port
        self.online = online

    def __eq__(self, other):
        return self.name == other.name and self.ip == other.ip and self.port == other.port

    def __hash__(self):
        return self.port ^ hash(self.name) ^ hash(self.ip)

    def __str__(self):
        return self.name + '(' + self.ip + ':' + str(self.port) + ')'


class MessageUnit:
    def __init__(self, timestamp: str, sender: str, content: str):
        self.timestamp = timestamp
        self.sender = sender
        self.content = content

    def __eq__(self, other):
        return self.timestamp == other.timestamp and self.sender == other.sender and self.content == other.sender

    def __hash__(self):
        # 将浮点数属性的哈希值转换为整数，然后与两个字符串属性的哈希值进行异或操作
        # timestamp = hash(self.timestamp) % (2 ** 32)  # 取余避免溢出
        return hash(self.timestamp) ^ hash(self.sender) ^ hash(self.content)


class PrivateChat:
    '''私聊消息'''

    def __init__(self, chat_name: str = ''):
        # 对应消息发布时间、发布人以及消息内容
        self.message_unit_list: List[MessageUnit] = []
        self.chat_name: str = chat_name
        self.online_or_not: bool = True

    @classmethod
    def check_instance(cls, obj):
        return isinstance(obj, cls)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.chat_name == other.chat_name


class GroupChat:
    '''群聊消息'''

    def __init__(self):
        self.message_unit_list: List[MessageUnit] = []
        self.chat_name: str = ''
        self.participants: List[str] = []

    @classmethod
    def check_instance(cls, obj):
        return isinstance(obj, cls)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        return self.chat_name == other.chat_name


class Data:
    '''单例数据库'''
    _instance = None  # 保存唯一实例的类变量
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance:
            return cls._instance

        with cls._lock:
            cls._instance = object.__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):
            with self._lock:
                self.local_peer: Union[PeerNode, None] = None
                self.peer_dict: Dict[str, PeerNode] = dict()
                self.private_chat_dict: Dict[str, PrivateChat] = dict()
                self.group_chat_dict: Dict[str, GroupChat] = dict()
                self.rwmutex_peer_dict = ReadWriteLock()
                self.rwmutex_private_chat_dict: ReadWriteLock = ReadWriteLock()
                self.rwmutex_group_chat_dict: ReadWriteLock = ReadWriteLock()

                self._initialized: bool = True
                self.server_thread = None

                # 保存定时器
                self.store_interval: float = 5
                self.store_timer: Union[threading.Timer, None] = None
                # '/home/learner/PycharmProjects/p2pChatRoom/DSFinalHW/Cache'
                self.data_cache_root: str = os.path.join(os.getcwd(), 'Cache')
                if not os.path.exists(self.data_cache_root):
                    os.mkdir(self.data_cache_root)

                # Gossip中一个节点承担的发送任务，主要是群聊消息的发送
                self.gossip_k = 2

    def set_local_peer(self, name: str, ip: str, port: int) -> bool:
        self.local_peer = PeerNode(name, ip, port)
        return True

    def iter_peer_dict(self) -> Generator[PeerNode, None, None]:
        for peer in self.peer_dict.values():
            yield peer

    def add_default_private_chat(self, chat_name: str, online: bool = True) -> bool:
        self.rwmutex_private_chat_dict.acquire_write()
        if self.private_chat_dict.get(chat_name) is not None:
            self.rwmutex_private_chat_dict.release_write()
            return False
        self.private_chat_dict[chat_name] = PrivateChat(chat_name)
        self.private_chat_dict[chat_name].online_or_not = online
        self.rwmutex_private_chat_dict.release_write()
        return True

    def append_peer(self, name: str, ip: str, port: int, online: bool = True) -> bool:
        self.rwmutex_peer_dict.acquire_write()
        peer = self.peer_dict.get(name)
        if peer is not None:
            peer.ip = ip
            peer.port = port
            peer.online = online
            self.rwmutex_peer_dict.release_write()
            self.set_private_chat_status(peer.name, online)
            return False
        self.peer_dict[name] = PeerNode(name, ip, port, online)
        self.rwmutex_peer_dict.release_write()
        if name != self.local_peer.name:
            self.add_default_private_chat(name, online)
        return True

    def get_peer(self, name: str) -> Union[PeerNode, None]:
        return self.peer_dict.get(name)

    def if_peer_online(self, name: str) -> bool:
        return True if (self.peer_dict.get(name) is not None and self.peer_dict.get(name).online) else False

    def get_private_chat(self, chat_name: str) -> Union[PrivateChat, None]:
        return self.private_chat_dict.get(chat_name)

    def get_group_chat(self, chat_name: str) -> Union[GroupChat, None]:
        return self.group_chat_dict.get(chat_name)

    def add_private_chat_message_unit(self, chat_name: str, message_unit: MessageUnit) -> bool:
        chat = self.private_chat_dict.get(chat_name)
        if chat is None:
            return False
        chat.message_unit_list.append(message_unit)

    def set_peer_online(self, name: str) -> bool:
        if self.peer_dict.get(name) is None:
            return False
        if self.peer_dict[name].online:
            self.set_private_chat_status(name, True)
            return False
        self.peer_dict[name].online = True
        private_chat = self.private_chat_dict.get(name)
        if private_chat is not None:
            private_chat.online_or_not = True
        else:
            self.add_default_private_chat(name)
        return True

    def set_private_chat_status(self, chat_name: str, online: bool) -> bool:
        private_chat = self.private_chat_dict.get(chat_name)
        if private_chat is not None:
            private_chat.online_or_not = online
            return True
        return False

    def iter_private_chat(self) -> Generator[PrivateChat, None, None]:
        for private_chat in self.private_chat_dict.values():
            yield private_chat

    def iter_group_chat(self) -> Generator[GroupChat, None, None]:
        for group_chat in self.group_chat_dict.values():
            yield group_chat

    def get_last_timestamp(self, chat_name: str) -> str:
        chat = self.private_chat_dict.get(chat_name)
        if chat is None:
            chat = self.group_chat_dict.get(chat_name)
        if chat is not None:
            return '0' if len(chat.message_unit_list) == 0 else chat.message_unit_list[-1].timestamp
        return '0'

    def get_message_unit_after_timestamp(self, chat_name: str, timestamp: str) -> List[MessageUnit]:
        chat = self.private_chat_dict.get(chat_name)
        if chat is None:
            chat = self.group_chat_dict.get(chat_name)

        if chat is not None:
            s = 0
            for message_unit in chat.message_unit_list:
                if message_unit.timestamp > timestamp:
                    break
                s += 1
            return chat.message_unit_list[s:len(chat.message_unit_list)]
        return []

    def add_group_chat(self, group_chat: GroupChat) -> bool:
        if self.group_chat_dict.get(group_chat.chat_name) is not None:
            return False
        self.rwmutex_group_chat_dict.acquire_write()
        self.group_chat_dict[group_chat.chat_name] = group_chat
        self.rwmutex_group_chat_dict.release_write()
        return True

    def add_default_group_chat(self, chat_name: str, participants: List[str]) -> bool:
        group_chat = GroupChat()
        group_chat.chat_name = chat_name
        group_chat.participants = participants
        return self.add_group_chat(group_chat)

    def remove_participant(self, chat_name: str, participant: str) -> bool:
        group_chat = self.group_chat_dict[chat_name]
        if group_chat is not None:
            if participant in group_chat.participants:
                group_chat.participants.remove(participant)
                return True
        return False

    def remove_group_chat(self, chat_name: str) -> bool:
        self.rwmutex_group_chat_dict.acquire_write()
        ret = self.group_chat_dict.pop(chat_name, None)
        self.rwmutex_group_chat_dict.release_write()
        return ret is not None

    def add_message_unit(self, chat_name: str, timestamp: str, sender: str, content: str) -> bool:
        chat = self.private_chat_dict.get(chat_name)
        # if chat is None:
        #     chat = self.group_chat_dict.get(chat_name)
        if chat is not None:
            # 重复的消息
            if (len(chat.message_unit_list) > 0 and
                    (chat.message_unit_list[-1].timestamp == timestamp and
                     chat.message_unit_list[-1].sender == sender)):
                logging.warning(f'Duplicate message: {chat_name}: '
                                f'{sender}:{content}'
                                f'({timestamp})')
                return False
            self.rwmutex_private_chat_dict.acquire_write()
            chat.message_unit_list.append(MessageUnit(timestamp, sender, content))
            self.rwmutex_private_chat_dict.release_write()
            return True
        # 群聊
        chat = self.group_chat_dict.get(chat_name)
        if chat is not None:
            if (len(chat.message_unit_list) > 0 and
                    (chat.message_unit_list[-1].timestamp == timestamp and
                     chat.message_unit_list[-1].sender == sender)):
                return False
            self.rwmutex_group_chat_dict.acquire_write()
            chat.message_unit_list.append(MessageUnit(timestamp, sender, content))
            self.rwmutex_group_chat_dict.release_write()
            return True
        return False

    # 添加消息，并返回聊天对象
    def add_and_get_chat(self, chat_name: str, message_unit: MessageUnit) -> Union[PrivateChat, GroupChat, None]:
        chat = self.private_chat_dict.get(chat_name)
        if chat is not None:
            self.rwmutex_private_chat_dict.acquire_write()
            chat.message_unit_list.append(message_unit)
            self.rwmutex_private_chat_dict.release_write()
            return chat

        chat = self.group_chat_dict.get(chat_name)
        if chat is not None:
            self.rwmutex_group_chat_dict.acquire_write()
            chat.message_unit_list.append(message_unit)
            self.rwmutex_group_chat_dict.release_write()
            return chat
        return None

    # 节点下线
    def set_peer_offline(self, name: str) -> bool:
        peer = self.peer_dict.get(name)
        if peer is not None:
            self.rwmutex_peer_dict.acquire_write()
            peer.online = False
            self.rwmutex_peer_dict.release_write()
        else:
            return False
        chat = self.private_chat_dict.get(name)
        if chat is not None:
            self.rwmutex_private_chat_dict.acquire_write()
            chat.online_or_not = False
            self.rwmutex_private_chat_dict.release_write()
        return True
