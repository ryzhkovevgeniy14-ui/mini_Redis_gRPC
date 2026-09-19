from concurrent.futures import ThreadPoolExecutor

from mini_redis_grpc.store import KeyValueStore


def test_put_and_get() -> None:
    """Проверяет сохранение и получение значения по ключу."""

    store = KeyValueStore()

    store.put("name", "John", 0)

    assert store.get("name") == "John"


def test_get_missing_key() -> None:
    """Проверяет получение отсутствующего ключа."""

    store = KeyValueStore()

    assert store.get("missing") is None


def test_put_updates_existing_key() -> None:
    """Проверяет обновление значения существующего ключа."""

    store = KeyValueStore()

    store.put("name", "John", 0)
    store.put("name", "Alex", 0)

    assert store.get("name") == "Alex"


def test_delete_existing_key() -> None:
    """Проверяет удаление существующего ключа."""

    store = KeyValueStore()

    store.put("name", "John", 0)

    assert store.delete("name") is True
    assert store.get("name") is None


def test_delete_missing_key() -> None:
    """Проверяет удаление отсутствующего ключа."""

    store = KeyValueStore()

    assert store.delete("missing") is False


def test_get_before_ttl_expiration() -> None:
    """Проверяет получение значения до истечения TTL."""

    store = KeyValueStore()

    store.put("key", "value", 10)

    assert store.get("key") == "value"


def test_get_after_ttl_expiration(monkeypatch) -> None:
    """Проверяет, что значение недоступно после истечения TTL."""

    current_time = 100.0

    monkeypatch.setattr(
        "mini_redis_grpc.store.time.monotonic",
        lambda: current_time,
    )

    store = KeyValueStore()

    store.put("key", "value", 10)

    assert store.get("key") == "value"

    current_time = 111.0

    assert store.get("key") is None


def test_list_by_prefix() -> None:
    """Проверяет получение ключей, соответствующих указанному префиксу."""

    store = KeyValueStore()

    store.put("user:1", "John", 0)
    store.put("user:2", "Alex", 0)
    store.put("order:1", "Book", 0)

    assert store.list("user:") == [
        ("user:1", "John"),
        ("user:2", "Alex"),
    ]


def test_list_excludes_expired_keys(monkeypatch) -> None:
    """Проверяет, что истёкшие ключи не возвращаются при получении списка."""

    current_time = 100.0

    monkeypatch.setattr(
        "mini_redis_grpc.store.time.monotonic",
        lambda: current_time,
    )

    store = KeyValueStore()

    store.put("user:1", "John", 10)
    store.put("user:2", "Alex", 0)

    current_time = 111.0

    assert store.list("user:") == [
        ("user:2", "Alex"),
    ]
    assert store.get("user:1") is None


def test_lru_evicts_least_recently_used_key() -> None:
    """Проверяет удаление наименее недавно использованного ключа при переполнении."""

    store = KeyValueStore()

    for index in range(11):
        store.put(f"key:{index}", f"value:{index}", 0)

    assert store.get("key:0") is None
    assert store.get("key:10") == "value:10"


def test_get_updates_lru_order() -> None:
    """Проверяет, что получение ключа обновляет его позицию в LRU."""

    store = KeyValueStore()

    for index in range(10):
        store.put(f"key:{index}", f"value:{index}", 0)

    assert store.get("key:0") == "value:0"

    store.put("key:10", "value:10", 0)

    assert store.get("key:0") == "value:0"
    assert store.get("key:1") is None


def test_put_updates_lru_order() -> None:
    """Проверяет, что обновление ключа через Put обновляет его позицию в LRU."""

    store = KeyValueStore()

    for index in range(10):
        store.put(f"key:{index}", f"value:{index}", 0)

    store.put("key:0", "updated", 0)
    store.put("key:10", "value:10", 0)

    assert store.get("key:0") == "updated"
    assert store.get("key:1") is None


def test_zero_ttl_does_not_expire(monkeypatch) -> None:
    """Проверяет, что TTL со значением 0 отключает автоматическое истечение ключа."""

    current_time = 100.0

    monkeypatch.setattr(
        "mini_redis_grpc.store.time.monotonic",
        lambda: current_time,
    )

    store = KeyValueStore()

    store.put("key", "value", 0)

    current_time = 10000.0

    assert store.get("key") == "value"


def test_concurrent_puts_are_thread_safe() -> None:
    """Проверяет корректную работу хранилища при параллельных записях."""

    store = KeyValueStore()

    def put_value(index: int) -> None:
        store.put(f"key:{index}", f"value:{index}", 0)

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(put_value, range(100))

    assert len(store._data) == store.MAX_SIZE
