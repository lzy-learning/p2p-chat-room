import time
import os
import pickle
from local_data import *
from rpc_server import *
import peer_pb2
from utils import logging, generate_file_name, generate_name


def store_local_data():
    data = Data()
    with open(os.path.join(data.data_cache_root,
                           generate_file_name(data.local_peer.name, data.local_peer.ip, data.local_peer.port)),
              'wb') as pkl_fp:
        pickle.dump(data.peer_dict, pkl_fp)
        pickle.dump(data.private_chat_dict, pkl_fp)
        pickle.dump(data.group_chat_dict, pkl_fp)
    data.store_timer = threading.Timer(data.store_interval, store_local_data)
    data.store_timer.start()


# 为了方便，我们从缓存中优先获取对应姓名
def get_name(ip, port):
    data = Data()
    cache_file_list = os.listdir(data.data_cache_root)
    for cache_file in cache_file_list:
        if cache_file.endswith(f'{ip}_{str(port)}.pkl'):
            return cache_file.split('_')[0]
    return generate_name()


def init(name, server_ip, server_port):
    data = Data()

    data.set_local_peer(name, server_ip, server_port)
    data.server_thread = GRPCServerThread()
    data.server_thread.start()
    time.sleep(0.5)

    data_cache_path = os.path.join(data.data_cache_root,
                                   generate_file_name(data.local_peer.name, data.local_peer.ip, data.local_peer.port))
    # 如果存在则加载本地文件
    if os.path.exists(data_cache_path):
        with open(data_cache_path, 'rb') as pkl_fp:
            data.peer_dict = pickle.load(pkl_fp)
            data.private_chat_dict = pickle.load(pkl_fp)
            data.group_chat_dict = pickle.load(pkl_fp)

        # 如果自己的IP和Port发生改变，则也要做出相应调整
        data.append_peer(data.local_peer.name, data.local_peer.ip, data.local_peer.port)

        # 1.同步对等节点信息
        for peer in data.iter_peer_dict():
            if peer.name == data.local_peer.name:
                continue

            channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
            stub = peer_pb2_grpc.PeerStub(channel)
            try:
                response = stub.GetPeers(
                    peer_pb2.GetPeersRequest(
                        name=data.local_peer.name,
                        ip=data.local_peer.ip,
                        port=data.local_peer.port
                    )
                )
                for other_peer in response.peer_list:
                    data.append_peer(other_peer.name, other_peer.ip, other_peer.port)

            except grpc.RpcError as e:
                logging.exception('=======================in init(GetPeerList): %s', e)
                data.set_peer_offline(peer.name)

        # 2. 同步群聊消息
        for group_chat in data.iter_group_chat():
            for participant in group_chat.participants:
                if participant == data.local_peer.name:
                    continue
                peer = data.get_peer(participant)
                if peer is None:
                    continue
                channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
                stub = peer_pb2_grpc.PeerStub(channel)
                try:
                    response = stub.SyncChat(
                        peer_pb2.SyncChatRequest(
                            chat_name=group_chat.chat_name,
                            timestamp='0' if len(group_chat.message_unit_list) == 0 else
                            group_chat.message_unit_list[-1].timestamp
                        )
                    )
                    if response.code != 1:
                        continue
                    for message_unit in response.message_unit_list:
                        group_chat.message_unit_list.append(
                            MessageUnit(message_unit.timestamp, message_unit.sender, message_unit.content)
                        )
                    break
                except grpc.RpcError as e:
                    logging.exception('=======================in init(SyncChat): %s', e)

        # 3. 如果当初是异常下线则同步私聊消息，否则不用，因为如果是正常下线会告知对方，对方就不会再发送消息过来
        for peer in data.iter_peer_dict():
            if peer.name == data.local_peer.name:
                continue

            channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
            stub = peer_pb2_grpc.PeerStub(channel)
            try:
                response = stub.SendOnlineStatus(
                    peer_pb2.SendOnlineStatusRequest(
                        name=data.local_peer.name, ip=data.local_peer.ip, port=data.local_peer.port, online=True
                    )
                )

                data.set_peer_online(peer.name)
                # 如果当时是异常下线，则同步该私聊消息
                if response.code == 2:
                    try:
                        response = stub.SyncChat(
                            peer_pb2.SyncChatRequest(
                                chat_name=data.local_peer.name,
                                timestamp=data.get_last_timestamp(peer.name)
                            )
                        )
                        for message_unit in response.message_unit_list:
                            data.add_private_chat_message_unit(
                                peer.name,
                                MessageUnit(message_unit.timestamp, message_unit.sender, message_unit.content)
                            )
                    except grpc.RpcError as e:
                        logging.exception(
                            '=======================in init(SendOnlineStatus)(SyncChatRequest): %s',
                            e)
            except grpc.RpcError as e:
                logging.exception('=======================in init(SendOnlineStatus): %s', e)

    # 第一次登陆
    else:
        logging.info('no cache data')
        data.append_peer(data.local_peer.name, data.local_peer.ip, data.local_peer.port)
    # 开启一个存储消息的线程，周期性存储消息
    data.store_timer = threading.Timer(data.store_interval, store_local_data)
    data.store_timer.start()


# 连接到另一个对等节点，返回1代表成功，0代表连接失败，-1代表网络中有重复节点
def connect_peer_node(ip: str, port: int) -> int:
    data = Data()
    channel = grpc.insecure_channel(f'{ip}:{port}')
    stub = peer_pb2_grpc.PeerStub(channel)
    try:
        response = stub.GetPeers(peer_pb2.GetPeersRequest(
            name=data.local_peer.name,
            ip=data.local_peer.ip,
            port=data.local_peer.port
        ))
    except grpc.RpcError as e:
        logging.exception('=======================in connect_peer_node(GetPeers): %s', e)
        return 0

    for peer in response.peer_list:
        if peer.name == data.local_peer.name:  # 节点名称重复
            return -1

    # 添加新节点，如果有需要的话要建立新消息(append_peer已实现该逻辑)
    for peer in response.peer_list:
        if peer.name == data.local_peer.name:
            continue
        data.append_peer(name=peer.name, ip=peer.ip, port=peer.port, online=peer.online)

    logging.info('Get peer list successfully!')
    for peer in data.iter_peer_dict():
        logging.info(f'name: {peer.name}, address: {peer.ip}:{peer.port}')

    return 1


# 获取节点列表成功后需要和其他节点广播自己的存在
def broadcast_my_existence() -> bool:
    data = Data()
    if len(data.peer_dict.values()) == 1:
        logging.error('peer list empty!')
        return False
    for peer in data.iter_peer_dict():
        if peer.name == data.local_peer.name:
            continue
        channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
        stub = peer_pb2_grpc.PeerStub(channel)
        try:
            response = stub.SendOnlineStatus(
                peer_pb2.SendOnlineStatusRequest(
                    name=data.local_peer.name,
                    ip=data.local_peer.ip,
                    port=data.local_peer.port,
                    online=True
                )
            )
        except grpc.RpcError as e:
            logging.exception('=======================in broadcast_my_existence(SendOnlineStatus): %s', e)
    return True


# 获取所有聊天列表
def get_chat_list():
    data = Data()
    chat_list: List[str] = [private_chat.chat_name for private_chat in data.iter_private_chat()
                            if private_chat.online_or_not] + \
                           [group_chat.chat_name for group_chat in data.iter_group_chat()]
    return chat_list


# 获取消息条数
def get_message_count(chat_name: Union[str, None]) -> int:
    if chat_name is not None:
        data = Data()
        chat = data.private_chat_dict.get(chat_name)
        if chat is None:
            chat = data.group_chat_dict.get(chat_name)
        if chat is None:
            return -1
        return len(chat.message_unit_list)
    return -1


# 获取聊天对应的聊天记录
def get_chat_info(chat_name: str, k: int = -1) -> Union[List[MessageUnit], None]:
    data = Data()
    if chat_name.endswith('(Group)'):
        message = data.get_group_chat(chat_name)
    else:
        message = data.get_private_chat(chat_name)
    if message is None:
        return None
    if k != -1 and k > len(message.message_unit_list):
        return message.message_unit_list[-k:]
    return message.message_unit_list


# 创建群聊
def create_group(group_name: str, peer_name_list: List[str]) -> bool:
    data = Data()
    group_chat = GroupChat()
    group_chat.chat_name = group_name + '(Group)'
    group_chat.participants = peer_name_list
    group_chat.participants.append(data.local_peer.name)
    data.add_group_chat(group_chat)

    # 发送给远端该创建消息
    for participant in group_chat.participants:
        if data.local_peer.name == participant:
            continue
        peer = data.get_peer(participant)
        if peer is not None:
            channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
            stub = peer_pb2_grpc.PeerStub(channel)
            try:
                response = stub.CreateGroup(
                    peer_pb2.CreateGroupRequest(
                        chat_name=group_chat.chat_name,
                        participants=group_chat.participants
                    )
                )
            except grpc.RpcError as e:
                logging.exception('=======================in create_group(CreateGroupChat): %s', e)
    return True


# 加入群聊
def join_group(chat_name: str) -> bool:
    data = Data()
    # 加入群聊的时候用户只提供名称，因此需要向其他所有对等节点询问该群聊
    for peer in data.iter_peer_dict():
        if peer.name == data.local_peer.name:
            continue
        channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
        stub = peer_pb2_grpc.PeerStub(channel)
        try:
            response = stub.JoinGroup(
                peer_pb2.JoinGroupRequest(
                    chat_name=chat_name,
                    name=data.local_peer.name,
                    ip=data.local_peer.ip,
                    port=data.local_peer.port,
                    need_group_chat_data=True
                )
            )
            if response.code == 1:
                group_chat = GroupChat()
                group_chat.chat_name = response.group_chat_data.chat_name
                group_chat.participants = list(response.group_chat_data.participants)
                group_chat.message_unit_list = [
                    MessageUnit(message_unit.timestamp, message_unit.sender, message_unit.content)
                    for message_unit in response.group_chat_data.message_unit_list]
                data.add_group_chat(group_chat)
                # 还需要向群内其他成员发送自己的加入消息
                for participant in group_chat.participants:
                    if participant == data.local_peer.name:
                        continue
                    peer = data.get_peer(participant)
                    if peer is not None:
                        channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
                        stub = peer_pb2_grpc.PeerStub(channel)
                        try:
                            response = stub.JoinGroup(
                                peer_pb2.JoinGroupRequest(
                                    chat_name=chat_name,
                                    name=data.local_peer.name,
                                    ip=data.local_peer.ip,
                                    port=data.local_peer.port,
                                    need_group_chat_data=False
                                )
                            )
                        except grpc.RpcError as e:
                            logging.exception('=======================in join_group(JoinGroup): %s', e)
                return True
        except grpc.RpcError as e:
            logging.exception('=======================in join_group(JoinGroup(Request Data)): %s', e)
    return False


def quit_group(chat_name: str) -> bool:
    data = Data()
    group_chat = data.get_group_chat(chat_name)
    if group_chat is not None:
        for participant in group_chat.participants:
            if participant == data.local_peer.name:
                continue
            peer = data.get_peer(participant)
            if peer is not None:
                channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
                stub = peer_pb2_grpc.PeerStub(channel)
                try:
                    response = stub.QuitGroup(
                        peer_pb2.QuitGroupRequest(
                            chat_name=chat_name,
                            name=data.local_peer.name
                        )
                    )
                except grpc.RpcError as e:
                    logging.exception('=======================in quit_group(QuitGroup): %s', e)
        data.remove_group_chat(chat_name)
        return True
    return False


def send_message(chat_name: str, message_content: str) -> bool:
    data = Data()
    # 在外面生成消息单元是合理的，因为不知道data.message_list什么时候处于繁忙状态导致写的时间被推迟，此时消息发布时间就不准确了
    message_unit = MessageUnit(f'{time.time():.5f}', data.local_peer.name, message_content)
    chat = data.add_and_get_chat(chat_name, message_unit)

    if chat is None:
        logging.error(f'Send to {chat_name} failed.')
        return False
    logging.info(f'{chat_name}==>{message_content}')

    # 私聊
    if isinstance(chat, PrivateChat):
        peer = data.get_peer(chat_name)
        channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
        stub = peer_pb2_grpc.PeerStub(channel)
        send_message_unit = peer_pb2.MessageUnit(
            timestamp=message_unit.timestamp,
            sender=message_unit.sender,
            content=message_unit.content
        )

        # 注意这里的chat_name应该是自己的名称，因为在对方看来是在和自己聊天，所以私聊的名称应该是对方的名称比较合理
        try:
            cur_time = time.time()
            response = stub.SendMessage(
                peer_pb2.SendMessageRequest(
                    chat_name=data.local_peer.name,
                    message_unit=send_message_unit,
                    had_received_list=None
                )
            )
            # print(f'now: {cur_time:.6f}')
            # print(f'{data.local_peer.name} sends message to {peer.name}({peer.ip}:{peer.port}):')
        except grpc.RpcError as e:
            logging.exception('=======================in send_message(SendMessage): %s', e)

    else:  # 群聊
        # 选择发送对方的列表，发送对方列表是参与群聊且在线的对等节点，选择k个
        sending_list = [participant for participant in chat.participants if
                        (lambda p: p != data.local_peer.name and data.if_peer_online(participant))(participant)][
                       :data.gossip_k]
        sending_list.append(data.local_peer.name)
        for participant in sending_list:
            if participant == data.local_peer.name:
                continue
            peer = data.get_peer(participant)
            if peer is None:
                continue

            channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
            stub = peer_pb2_grpc.PeerStub(channel)
            try:
                send_message_request = peer_pb2.SendMessageRequest()
                send_message_request.chat_name = chat_name
                send_message_request.message_unit.timestamp = message_unit.timestamp
                send_message_request.message_unit.sender = message_unit.sender
                send_message_request.message_unit.content = message_unit.content
                send_message_request.had_received_list.extend(sending_list)
                cur_time = time.time()
                # print(f'cur peer: {data.local_peer.name}, now: {cur_time:.6f}')
                # print(f'{data.local_peer.name} sends message to {peer.name}({peer.ip}:{peer.port}):')
                response = stub.SendMessage(
                    send_message_request
                )
            except grpc.RpcError as e:
                logging.exception('=======================in send_message(SendMessage): %s', e)
    logging.info(f'Send to {chat_name} successfully. {message_content}')
    return True


def normal_quit() -> None:
    data = Data()
    data.store_timer.cancel()
    with open(os.path.join(data.data_cache_root,
                           generate_file_name(data.local_peer.name, data.local_peer.ip, data.local_peer.port)),
              'wb') as pkl_fp:
        pickle.dump(data.peer_dict, pkl_fp)
        pickle.dump(data.private_chat_dict, pkl_fp)
        pickle.dump(data.group_chat_dict, pkl_fp)
    for peer in data.iter_peer_dict():
        if peer.name == data.local_peer.name or not peer.online:
            continue
        channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
        stub = peer_pb2_grpc.PeerStub(channel)
        logging.info(f'Quit message sended to {peer.name}({peer.ip}:{peer.port})')
        try:
            response = stub.Quit(
                peer_pb2.QuitRequest(
                    name=data.local_peer.name
                )
            )
            logging.info(f'quit message send to {peer.name}. get_it?: {response.code}')
        except grpc.RpcError as e:
            logging.exception('=======================in normal_quit(Quit): %s', e)
