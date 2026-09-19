import time
from collections import OrderedDict
from dataclasses import dataclass
from threading import Lock


@dataclass
class StoredValue:
    """Запись хранилища с её значением и временем истечения TTL."""

    value: str
    expires_at: float | None


class KeyValueStore:
    """Потокобезопасное хранилище с TTL и вытеснением по алгоритму LRU."""

    MAX_SIZE = 10

    def __init__(self) -> None:
        self._data: OrderedDict[str, StoredValue] = OrderedDict()
        self._lock = Lock()

    def put(self, key: str, value: str, ttl_seconds: int) -> None:
        """Добавляет или обновляет ключ и устанавливает для него TTL."""

        expires_at = time.monotonic() + ttl_seconds if ttl_seconds > 0 else None

        with self._lock:
            self._data[key] = StoredValue(
                value=value,
                expires_at=expires_at,
            )
            self._data.move_to_end(key)

            if len(self._data) > self.MAX_SIZE:
                self._data.popitem(last=False)

    def get(self, key: str) -> str | None:
        """Возвращает значение по ключу или None, если ключ отсутствует или истёк."""

        with self._lock:
            stored_value = self._data.get(key)

            if stored_value is None:
                return None

            if self._is_expired(stored_value):
                del self._data[key]
                return None

            self._data.move_to_end(key)
            return stored_value.value

    def delete(self, key: str) -> bool:
        """Удаляет ключ и возвращает True, если он существовал."""

        with self._lock:
            if key not in self._data:
                return False

            del self._data[key]
            return True

    def list(self, prefix: str) -> list[tuple[str, str]]:
        """Возвращает неистёкшие пары ключ-значение с указанным префиксом."""

        with self._lock:
            result = []

            for key in list(self._data):
                stored_value = self._data[key]

                if self._is_expired(stored_value):
                    del self._data[key]
                    continue

                if key.startswith(prefix):
                    result.append((key, stored_value.value))

            return result

    @staticmethod
    def _is_expired(stored_value: StoredValue) -> bool:
        """Проверяет, истёк ли TTL записи."""

        if stored_value.expires_at is None:
            return False

        return time.monotonic() >= stored_value.expires_at
