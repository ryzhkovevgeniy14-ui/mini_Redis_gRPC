from concurrent import futures

import grpc

from mini_redis_grpc import kvstore_pb2_grpc
from mini_redis_grpc.grpc_server import KeyValueStoreService
from mini_redis_grpc.store import KeyValueStore


def serve() -> None:
    """Запускает gRPC-сервер KeyValueStore на порту 8000."""

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    store = KeyValueStore()
    service = KeyValueStoreService(store)

    kvstore_pb2_grpc.add_KeyValueStoreServicer_to_server(
        service,
        server,
    )

    server.add_insecure_port("[::]:8000")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
