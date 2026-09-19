from concurrent import futures

import grpc
import pytest

from mini_redis_grpc import kvstore_pb2_grpc
from mini_redis_grpc.grpc_server import KeyValueStoreService
from mini_redis_grpc.store import KeyValueStore


@pytest.fixture
def grpc_stub():
    """Создаёт gRPC-сервер и stub для интеграционных тестов."""

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))

    store = KeyValueStore()

    kvstore_pb2_grpc.add_KeyValueStoreServicer_to_server(
        KeyValueStoreService(store),
        server,
    )

    port = server.add_insecure_port("localhost:0")
    server.start()

    channel = grpc.insecure_channel(f"localhost:{port}")
    stub = kvstore_pb2_grpc.KeyValueStoreStub(channel)

    yield stub

    channel.close()

    server.stop(0)
