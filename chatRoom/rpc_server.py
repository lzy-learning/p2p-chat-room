import logging
import time

import peer_pb2_grpc
import peer_pb2
import grpc
from local_data import Data, MessageUnit
import threading
from concurrent import futures


class PeerServer(peer_pb2_grpc.PeerServicer):
    def GetPeers(self, request, context):
        data = Data()
        sending_peer_list = [
            peer_pb2.PeerNode(
                name=peer.name, ip=peer.ip, port=peer.port, online=peer.online
            ) for peer in data.iter_peer_dict()
        ]
        return peer_pb2.GetPeersResponse(
            peer_list=sending_peer_list
        )

    def SyncChat(self, request, context):
        data = Data()
        message_unit_list = data.get_message_unit_after_timestamp(request.chat_name, request.timestamp)
        sending_message_unit_list = [
            peer_pb2.MessageUnit(
                timestamp=message_unit.timestamp, sender=message_unit.sender, content=message_unit.content
            ) for message_unit in message_unit_list
        ]
        return peer_pb2.SyncChatResponse(
            code=1,
            message_unit_list=sending_message_unit_list
        )

    def SendOnlineStatus(self, request, context):
        data = Data()
        peer = data.get_peer(request.name)
        logging.info(f'receive {request.name}({request.ip}:{request.port}) is online...')
        if peer is not None:
            peer.ip = request.ip
            peer.port = request.port
            if data.set_peer_online(request.name):
                return peer_pb2.SendOnlineStatusResponse(code=1)
            else:
                return peer_pb2.SendOnlineStatusResponse(code=2)
        else:
            data.append_peer(request.name, request.ip, request.port, request.online)
            return peer_pb2.SendOnlineStatusResponse(code=0)

    def CreateGroup(self, request, context):
        data = Data()
        flag = data.add_default_group_chat(request.chat_name, list(request.participants))
        return peer_pb2.CreateGroupResponse(code=1 if flag else 0)

    def JoinGroup(self, request, context):
        data = Data()
        group_chat = data.get_group_chat(request.chat_name)
        if group_chat is None:
            return peer_pb2.JoinGroupResponse(
                code=2,
                group_chat_data=None
            )
        if data.get_peer(request.name) is None:
            data.append_peer(request.name, request.ip, request.port)
        group_chat.participants.append(request.name)

        sending_group_chat = None
        if request.need_group_chat_data is True:
            sending_group_chat = peer_pb2.GroupChat()
            sending_group_chat.chat_name = group_chat.chat_name
            sending_group_chat.participants.extend(group_chat.participants)
            sending_group_chat.message_unit_list.extend([
                peer_pb2.MessageUnit(
                    timestamp=message_unit.timestamp, sender=message_unit.sender, content=message_unit.content
                )
                for message_unit in group_chat.message_unit_list
            ])
        return peer_pb2.JoinGroupResponse(
            code=1,
            group_chat_data=sending_group_chat
        )

    def QuitGroup(self, request, context):
        data = Data()
        flag = data.remove_participant(request.chat_name, request.name)
        data.add_message_unit(request.chat_name, f'{time.time():.5f}', '',
                              f'\n======{request.name} quit group======\n')
        return peer_pb2.QuitGroupResponse(code=1 if flag else 2)

    def SendMessage(self, request, context):
        cur_time = time.time()
        data = Data()
        print(f'cur peer: {data.local_peer.name}, now: {cur_time:.6f}')
        print(f'{data.local_peer.name} receive message from {request.chat_name}')
        flag = data.add_message_unit(
            request.chat_name,
            request.message_unit.timestamp,
            request.message_unit.sender,
            request.message_unit.content,
        )

        logging.info(
            f'receive message from {request.chat_name}: {request.message_unit.sender}, {request.message_unit.content}({request.message_unit.timestamp})')
        # 如果是群聊，则要承担发送给其他节点的任务
        if request.had_received_list is not None and len(request.had_received_list) != 0:
            logging.info("group chat gossip")
            thread = threading.Thread(target=PeerServer.SendGroupMessage(request))
            thread.start()
        return peer_pb2.SendMessageResponse(code=1 if flag else 2)

    @staticmethod
    def SendGroupMessage(request):
        data = Data()
        had_received_set = set()
        for had_received in request.had_received_list:
            had_received_set.add(had_received)
        select_peer = [peer for peer in data.iter_peer_dict() if peer.name not in had_received_set and
                       peer.online and peer.name != data.local_peer.name][:data.gossip_k]
        logging.info(f'========================================================')
        logging.info(f'{data.local_peer.name}:')
        logging.info(f'had received list: {had_received_set}')
        logging.info(f'select peer list: {[peer.name for peer in select_peer]}')

        had_received_list = list(had_received_set) + [peer.name for peer in select_peer]
        for peer in select_peer:
            if peer.name == data.local_peer.name:
                continue
            channel = grpc.insecure_channel(f'{peer.ip}:{peer.port}')
            stub = peer_pb2_grpc.PeerStub(channel)
            try:
                send_message_request = peer_pb2.SendMessageRequest()
                send_message_request.chat_name = request.chat_name
                # send_message_request.message_unit = peer_pb2.MessageUnit(
                #     timestamp=request.message_unit.timestamp,
                #     sender=request.message_unit.sender,
                #     content=request.message_unit.content
                # )
                send_message_request.message_unit.timestamp = request.message_unit.timestamp
                send_message_request.message_unit.sender = request.message_unit.sender
                send_message_request.message_unit.content = request.message_unit.content

                send_message_request.had_received_list.extend(had_received_list)
                response = stub.SendMessage(
                    send_message_request
                )
            except grpc.RpcError as e:
                logging.exception('=======================in SendGroupMessage(SendMessage): %s', e)

    def Quit(self, request, context):
        data = Data()
        flag = data.set_peer_offline(request.name)
        return peer_pb2.QuitResponse(code=1 if flag else 2)


class GRPCServerThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stop_event = threading.Event()
        self.server = None

    def run(self):
        data = Data()
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
        peer_pb2_grpc.add_PeerServicer_to_server(PeerServer(), self.server)

        self.server.add_insecure_port(f'{data.local_peer.ip}:{data.local_peer.port}')
        self.server.start()
        while not self.stop_event.is_set():
            pass

        self.server.stop(0)

    def stop_server(self):
        self.stop_event.set()


def start_grpc_server(server_ip, server_port):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    peer_pb2_grpc.add_PeerServicer_to_server(PeerServer(), server)

    server.add_insecure_port(f'{server_ip}:{server_port}')
    server.start()
    server.wait_for_termination()
