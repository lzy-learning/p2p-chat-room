# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import peer_pb2 as peer__pb2


class PeerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.GetPeers = channel.unary_unary(
                '/peer.Peer/GetPeers',
                request_serializer=peer__pb2.GetPeersRequest.SerializeToString,
                response_deserializer=peer__pb2.GetPeersResponse.FromString,
                )
        self.SyncChat = channel.unary_unary(
                '/peer.Peer/SyncChat',
                request_serializer=peer__pb2.SyncChatRequest.SerializeToString,
                response_deserializer=peer__pb2.SyncChatResponse.FromString,
                )
        self.SendOnlineStatus = channel.unary_unary(
                '/peer.Peer/SendOnlineStatus',
                request_serializer=peer__pb2.SendOnlineStatusRequest.SerializeToString,
                response_deserializer=peer__pb2.SendOnlineStatusResponse.FromString,
                )
        self.CreateGroup = channel.unary_unary(
                '/peer.Peer/CreateGroup',
                request_serializer=peer__pb2.CreateGroupRequest.SerializeToString,
                response_deserializer=peer__pb2.CreateGroupResponse.FromString,
                )
        self.JoinGroup = channel.unary_unary(
                '/peer.Peer/JoinGroup',
                request_serializer=peer__pb2.JoinGroupRequest.SerializeToString,
                response_deserializer=peer__pb2.JoinGroupResponse.FromString,
                )
        self.QuitGroup = channel.unary_unary(
                '/peer.Peer/QuitGroup',
                request_serializer=peer__pb2.QuitGroupRequest.SerializeToString,
                response_deserializer=peer__pb2.QuitGroupResponse.FromString,
                )
        self.SendMessage = channel.unary_unary(
                '/peer.Peer/SendMessage',
                request_serializer=peer__pb2.SendMessageRequest.SerializeToString,
                response_deserializer=peer__pb2.SendMessageResponse.FromString,
                )
        self.Quit = channel.unary_unary(
                '/peer.Peer/Quit',
                request_serializer=peer__pb2.QuitRequest.SerializeToString,
                response_deserializer=peer__pb2.QuitResponse.FromString,
                )


class PeerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def GetPeers(self, request, context):
        """获取对等节点列表
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SyncChat(self, request, context):
        """根据时间戳同步某则消息
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendOnlineStatus(self, request, context):
        """发送自己的上线消息
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateGroup(self, request, context):
        """创建群聊
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def JoinGroup(self, request, context):
        """加入群聊
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def QuitGroup(self, request, context):
        """退出群聊
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendMessage(self, request, context):
        """发送消息
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Quit(self, request, context):
        """节点退出
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_PeerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'GetPeers': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPeers,
                    request_deserializer=peer__pb2.GetPeersRequest.FromString,
                    response_serializer=peer__pb2.GetPeersResponse.SerializeToString,
            ),
            'SyncChat': grpc.unary_unary_rpc_method_handler(
                    servicer.SyncChat,
                    request_deserializer=peer__pb2.SyncChatRequest.FromString,
                    response_serializer=peer__pb2.SyncChatResponse.SerializeToString,
            ),
            'SendOnlineStatus': grpc.unary_unary_rpc_method_handler(
                    servicer.SendOnlineStatus,
                    request_deserializer=peer__pb2.SendOnlineStatusRequest.FromString,
                    response_serializer=peer__pb2.SendOnlineStatusResponse.SerializeToString,
            ),
            'CreateGroup': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateGroup,
                    request_deserializer=peer__pb2.CreateGroupRequest.FromString,
                    response_serializer=peer__pb2.CreateGroupResponse.SerializeToString,
            ),
            'JoinGroup': grpc.unary_unary_rpc_method_handler(
                    servicer.JoinGroup,
                    request_deserializer=peer__pb2.JoinGroupRequest.FromString,
                    response_serializer=peer__pb2.JoinGroupResponse.SerializeToString,
            ),
            'QuitGroup': grpc.unary_unary_rpc_method_handler(
                    servicer.QuitGroup,
                    request_deserializer=peer__pb2.QuitGroupRequest.FromString,
                    response_serializer=peer__pb2.QuitGroupResponse.SerializeToString,
            ),
            'SendMessage': grpc.unary_unary_rpc_method_handler(
                    servicer.SendMessage,
                    request_deserializer=peer__pb2.SendMessageRequest.FromString,
                    response_serializer=peer__pb2.SendMessageResponse.SerializeToString,
            ),
            'Quit': grpc.unary_unary_rpc_method_handler(
                    servicer.Quit,
                    request_deserializer=peer__pb2.QuitRequest.FromString,
                    response_serializer=peer__pb2.QuitResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'peer.Peer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Peer(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def GetPeers(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/peer.Peer/GetPeers',
            peer__pb2.GetPeersRequest.SerializeToString,
            peer__pb2.GetPeersResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SyncChat(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/peer.Peer/SyncChat',
            peer__pb2.SyncChatRequest.SerializeToString,
            peer__pb2.SyncChatResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendOnlineStatus(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/peer.Peer/SendOnlineStatus',
            peer__pb2.SendOnlineStatusRequest.SerializeToString,
            peer__pb2.SendOnlineStatusResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def CreateGroup(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/peer.Peer/CreateGroup',
            peer__pb2.CreateGroupRequest.SerializeToString,
            peer__pb2.CreateGroupResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def JoinGroup(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/peer.Peer/JoinGroup',
            peer__pb2.JoinGroupRequest.SerializeToString,
            peer__pb2.JoinGroupResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def QuitGroup(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/peer.Peer/QuitGroup',
            peer__pb2.QuitGroupRequest.SerializeToString,
            peer__pb2.QuitGroupResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendMessage(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/peer.Peer/SendMessage',
            peer__pb2.SendMessageRequest.SerializeToString,
            peer__pb2.SendMessageResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Quit(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/peer.Peer/Quit',
            peer__pb2.QuitRequest.SerializeToString,
            peer__pb2.QuitResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)