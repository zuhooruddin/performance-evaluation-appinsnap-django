import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pymongo import MongoClient


DATA_DIR = Path("temp_storage")
DATA_DIR.mkdir(exist_ok=True)


class _FileStorage:
    @staticmethod
    def _file_path(collection: str) -> Path:
        return DATA_DIR / f"{collection}.json"

    @staticmethod
    def load(collection: str) -> Dict[str, Any]:
        file = _FileStorage._file_path(collection)
        if not file.exists():
            return {}
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save(collection: str, data: Dict[str, Any]) -> None:
        file = _FileStorage._file_path(collection)
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


class _MongoStorage:
    """
    Minimal key-value collection storage that matches the legacy file-backed API.

    Implementation detail:
    - Each "collection" is a MongoDB collection.
    - Each key maps to a document with `_id = key` and the stored value in `value`.
    - `load()` returns the whole collection as a dict[key] = value (legacy behavior).
    """

    _client: Optional[MongoClient] = None
    _db_name: str = "performance_eval"

    @classmethod
    def _db(cls):
        uri = os.getenv("MONGODB_URI")
        if not uri:
            raise RuntimeError("MONGODB_URI is not set")
        if cls._client is None:
            cls._client = MongoClient(uri)
        cls._db_name = os.getenv("MONGODB_DB", cls._db_name)
        return cls._client[cls._db_name]

    @classmethod
    def load(cls, collection: str) -> Dict[str, Any]:
        db = cls._db()
        out: Dict[str, Any] = {}
        for doc in db[collection].find({}, {"value": 1}):
            out[str(doc["_id"])] = doc.get("value")
        return out

    @classmethod
    def save(cls, collection: str, data: Dict[str, Any]) -> None:
        db = cls._db()
        col = db[collection]
        col.delete_many({})
        if data:
            col.insert_many([{"_id": str(k), "value": v} for k, v in data.items()])

    @classmethod
    def insert(cls, collection: str, key: str, value: Any) -> None:
        db = cls._db()
        db[collection].replace_one({"_id": str(key)}, {"_id": str(key), "value": value}, upsert=True)

    @classmethod
    def get(cls, collection: str, key: str) -> Any:
        db = cls._db()
        doc = db[collection].find_one({"_id": str(key)}, {"value": 1})
        return None if not doc else doc.get("value")

    @classmethod
    def get_all(cls, collection: str) -> Dict[str, Any]:
        return cls.load(collection)

    @classmethod
    def delete(cls, collection: str, key: str) -> None:
        db = cls._db()
        db[collection].delete_one({"_id": str(key)})


def _use_mongo() -> bool:
    val = os.getenv("USE_MONGO", "true").strip().lower()
    if val in {"0", "false", "no", "off"}:
        return False
    return bool(os.getenv("MONGODB_URI"))


class Storage:
    @staticmethod
    def load(collection: str) -> Dict[str, Any]:
        if _use_mongo():
            return _MongoStorage.load(collection)
        return _FileStorage.load(collection)

    @staticmethod
    def save(collection: str, data: Dict[str, Any]) -> None:
        if _use_mongo():
            return _MongoStorage.save(collection, data)
        return _FileStorage.save(collection, data)

    @staticmethod
    def insert(collection: str, key: str, value: Any) -> None:
        if _use_mongo():
            return _MongoStorage.insert(collection, key, value)
        data = _FileStorage.load(collection)
        data[str(key)] = value
        return _FileStorage.save(collection, data)

    @staticmethod
    def get(collection: str, key: str) -> Any:
        if _use_mongo():
            return _MongoStorage.get(collection, key)
        data = _FileStorage.load(collection)
        return data.get(str(key))

    @staticmethod
    def get_all(collection: str) -> Dict[str, Any]:
        return Storage.load(collection)

    @staticmethod
    def delete(collection: str, key: str) -> None:
        if _use_mongo():
            return _MongoStorage.delete(collection, key)
        data = _FileStorage.load(collection)
        if str(key) in data:
            del data[str(key)]
        return _FileStorage.save(collection, data)