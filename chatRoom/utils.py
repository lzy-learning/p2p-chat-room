import re
import threading
from concurrent import futures
import time
import random
import string
import socket
from typing import Union
import logging
import socket


# 打印所有信息
# logging.basicConfig(level=logging.INFO)

# 不打印信息
logging.basicConfig(level=logging.CRITICAL+1)


class ReadWriteLock(object):
    def __init__(self):
        self.__monitor = threading.Lock()
        self.__exclude = threading.Lock()
        self.readers = 0

    def acquire_read(self):
        with self.__monitor:
            self.readers += 1
            if self.readers == 1:
                self.__exclude.acquire()

    def release_read(self):
        with self.__monitor:
            self.readers -= 1
            if self.readers == 0:
                self.__exclude.release()

    def acquire_write(self):
        self.__exclude.acquire()

    def release_write(self):
        self.__exclude.release()


def generate_name() -> str:
    vowels: str = 'aeiou'
    consonants = ''.join(set(string.ascii_lowercase) - set(vowels))
    name: str = ''
    for i in range(random.randint(3, 8)):
        if i % 2 == 0:
            name += random.choice(consonants)
        else:
            name += random.choice(vowels)
    return name.capitalize()


def generate_content() -> str:
    length = random.randint(16, 32)
    random_str = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))
    return random_str


def if_ip_valid(ip: str) -> bool:
    if re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", ip):
        return True
    else:
        return False


def if_port_valid(port: Union[str, int]) -> bool:
    port = int(port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
        except socket.error:
            return False  # 端口被占用或者端口无效
    return True


def find_available_port(port_lb: int = 8080, port_ub: int = 65535) -> Union[int, None]:
    for port in range(port_lb, port_ub + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind((get_host_ip(), port))
            except socket.error:
                continue
            return port

    return None


def generate_file_name(name: str, ip: str, port: int) -> str:
    return f'{name}_{ip}_{str(port)}.pkl'


# 获取本地IP地址
def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


if __name__ == '__main__':
    rw_lock = ReadWriteLock()

    def get_read_lock():
        rw_lock.acquire_read()
        print("get read lock")
        time.sleep(3)
        rw_lock.release_read()


    def get_write_lock():
        rw_lock.acquire_write()
        print("get write lock")
        time.sleep(2)
        rw_lock.release_write()


    executor = futures.ThreadPoolExecutor(max_workers=12)
    executor.submit(get_read_lock)
    executor.submit(get_read_lock)
    executor.submit(get_read_lock)
    executor.submit(get_write_lock)
