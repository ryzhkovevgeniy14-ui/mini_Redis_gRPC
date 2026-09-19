import time

import grpc
import pytest

from mini_redis_grpc import kvstore_pb2


def test_put_and_get(grpc_stub):
    """Проверяет сохранение и получение значения через gRPC."""

    grpc_stub.Put(
        kvstore_pb2.PutRequest(
            key="user:1",
            value="Alex",
        )
    )

    response = grpc_stub.Get(
        kvstore_pb2.GetRequest(
            key="user:1",
        )
    )

    assert response.value == "Alex"


def test_get_missing_key_returns_not_found(grpc_stub):
    """Проверяет, что получение отсутствующего ключа возвращает NOT_FOUND."""

    with pytest.raises(grpc.RpcError) as error:
        grpc_stub.Get(
            kvstore_pb2.GetRequest(
                key="missing",
            )
        )

    assert error.value.code() == grpc.StatusCode.NOT_FOUND


def test_delete(grpc_stub):
    """Проверяет удаление ключа и последующий статус NOT_FOUND."""

    grpc_stub.Put(
        kvstore_pb2.PutRequest(
            key="user:1",
            value="Alex",
        )
    )

    grpc_stub.Delete(
        kvstore_pb2.DeleteRequest(
            key="user:1",
        )
    )

    with pytest.raises(grpc.RpcError) as error:
        grpc_stub.Get(
            kvstore_pb2.GetRequest(
                key="user:1",
            )
        )

    assert error.value.code() == grpc.StatusCode.NOT_FOUND


def test_list(grpc_stub):
    """Проверяет получение ключей и значений по префиксу через gRPC."""

    grpc_stub.Put(
        kvstore_pb2.PutRequest(
            key="user:1",
            value="Alex",
        )
    )
    grpc_stub.Put(
        kvstore_pb2.PutRequest(
            key="user:2",
            value="Bob",
        )
    )
    grpc_stub.Put(
        kvstore_pb2.PutRequest(
            key="product:1",
            value="Phone",
        )
    )

    response = grpc_stub.List(
        kvstore_pb2.ListRequest(
            prefix="user:",
        )
    )

    items = [(item.key, item.value) for item in response.items]

    assert items == [
        ("user:1", "Alex"),
        ("user:2", "Bob"),
    ]


def test_get_expired_key_returns_not_found(grpc_stub):
    """Проверяет, что получение ключа после истечения TTL возвращает NOT_FOUND."""

    grpc_stub.Put(
        kvstore_pb2.PutRequest(
            key="temporary",
            value="value",
            ttl_seconds=1,
        )
    )

    time.sleep(1.1)

    with pytest.raises(grpc.RpcError) as error:
        grpc_stub.Get(
            kvstore_pb2.GetRequest(
                key="temporary",
            )
        )

    assert error.value.code() == grpc.StatusCode.NOT_FOUND


def test_list_excludes_expired_keys(grpc_stub):
    """Проверяет, что List не возвращает ключи с истёкшим TTL."""

    grpc_stub.Put(
        kvstore_pb2.PutRequest(
            key="user:1",
            value="Alex",
            ttl_seconds=1,
        )
    )
    grpc_stub.Put(
        kvstore_pb2.PutRequest(
            key="user:2",
            value="Bob",
        )
    )

    time.sleep(1.1)

    response = grpc_stub.List(
        kvstore_pb2.ListRequest(
            prefix="user:",
        )
    )

    items = [(item.key, item.value) for item in response.items]

    assert items == [
        ("user:2", "Bob"),
    ]
