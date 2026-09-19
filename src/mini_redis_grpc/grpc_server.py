import grpc

from mini_redis_grpc import kvstore_pb2, kvstore_pb2_grpc
from mini_redis_grpc.store import KeyValueStore


class KeyValueStoreService(kvstore_pb2_grpc.KeyValueStoreServicer):
    """gRPC-адаптер для взаимодействия с KeyValueStore."""

    def __init__(self, store: KeyValueStore) -> None:
        self._store = store

    def Put(
        self,
        request: kvstore_pb2.PutRequest,
        context: grpc.ServicerContext,
    ) -> kvstore_pb2.PutResponse:
        """Добавляет или обновляет ключ в хранилище."""

        self._store.put(
            request.key,
            request.value,
            request.ttl_seconds,
        )

        return kvstore_pb2.PutResponse()

    def Get(
        self,
        request: kvstore_pb2.GetRequest,
        context: grpc.ServicerContext,
    ) -> kvstore_pb2.GetResponse:
        """Возвращает значение ключа или NOT_FOUND, если ключ отсутствует."""

        value = self._store.get(request.key)

        if value is None:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                "Key not found",
            )

        return kvstore_pb2.GetResponse(value=value)

    def Delete(
        self,
        request: kvstore_pb2.DeleteRequest,
        context: grpc.ServicerContext,
    ) -> kvstore_pb2.DeleteResponse:
        """Удаляет ключ из хранилища."""

        self._store.delete(request.key)

        return kvstore_pb2.DeleteResponse()

    def List(
        self,
        request: kvstore_pb2.ListRequest,
        context: grpc.ServicerContext,
    ) -> kvstore_pb2.ListResponse:
        """Возвращает ключи и значения с указанным префиксом."""

        items = self._store.list(request.prefix)

        return kvstore_pb2.ListResponse(
            items=[kvstore_pb2.KeyValue(key=key, value=value) for key, value in items]
        )
