"""
server/models/message_log.py — Message logging model (Sync PyMongo)
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from config.database import messages_col
from bson import ObjectId


@dataclass
class MessageLog:
    session_id: str
    message_id: str
    from_jid: str
    chat_jid: str
    body: str
    direction: str = "in"
    message_type: str = "text"
    is_command: bool = False
    command_name: Optional[str] = None
    is_group: bool = False
    group_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    media_url: Optional[str] = None
    _id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "MessageLog":
        return cls(
            session_id=data.get("session_id", ""),
            message_id=data.get("message_id", ""),
            from_jid=data.get("from_jid", ""),
            chat_jid=data.get("chat_jid", ""),
            body=data.get("body", ""),
            direction=data.get("direction", "in"),
            message_type=data.get("message_type", "text"),
            is_command=data.get("is_command", False),
            command_name=data.get("command_name"),
            is_group=data.get("is_group", False),
            group_id=data.get("group_id"),
            timestamp=data.get("timestamp", datetime.utcnow()),
            media_url=data.get("media_url"),
            _id=str(data.get("_id", "")),
        )

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id, "message_id": self.message_id,
            "from_jid": self.from_jid, "chat_jid": self.chat_jid,
            "body": self.body, "direction": self.direction,
            "message_type": self.message_type, "is_command": self.is_command,
            "command_name": self.command_name, "is_group": self.is_group,
            "group_id": self.group_id, "timestamp": self.timestamp,
            "media_url": self.media_url,
        }

    def save(self) -> bool:
        result = messages_col().insert_one(self.to_dict())
        self._id = str(result.inserted_id)
        return bool(result.inserted_id)

    @staticmethod
    def get_recent(session_id: str = "global", limit: int = 50) -> list["MessageLog"]:
        docs = messages_col().find({"session_id": session_id}).sort("timestamp", -1).limit(limit)
        return [MessageLog.from_dict(doc) for doc in docs]

    @staticmethod
    def get_by_jid(session_id: str, jid: str, limit: int = 100) -> list["MessageLog"]:
        docs = messages_col().find({
            "session_id": session_id,
            "$or": [{"from_jid": {"$regex": jid}}, {"chat_jid": {"$regex": jid}}]
        }).sort("timestamp", -1).limit(limit)
        return [MessageLog.from_dict(doc) for doc in docs]

    @staticmethod
    def get_conversations(session_id: str = "global", limit: int = 500) -> list[dict]:
        pipeline = [
            {"$match": {"session_id": session_id}},
            {"$sort": {"timestamp": -1}},
            {"$limit": limit},
            {"$group": {
                "_id": "$from_jid",
                "last_message": {"$first": "$body"},
                "timestamp": {"$first": "$timestamp"},
                "count": {"$sum": 1},
            }},
            {"$sort": {"timestamp": -1}},
        ]
        return list(messages_col().aggregate(pipeline))

    @staticmethod
    def search(session_id: str, query: str, limit: int = 50) -> list["MessageLog"]:
        docs = messages_col().find({
            "session_id": session_id,
            "body": {"$regex": query, "$options": "i"}
        }).sort("timestamp", -1).limit(limit)
        return [MessageLog.from_dict(doc) for doc in docs]

    @staticmethod
    def get_stats(session_id: str = "global") -> dict:
        pipeline = [
            {"$match": {"session_id": session_id}},
            {"$group": {
                "_id": None,
                "total": {"$sum": 1},
                "incoming": {"$sum": {"$cond": [{"$eq": ["$direction", "in"]}, 1, 0]}},
                "outgoing": {"$sum": {"$cond": [{"$eq": ["$direction", "out"]}, 1, 0]}},
                "commands": {"$sum": {"$cond": [{"$eq": ["$is_command", True]}, 1, 0]}},
            }},
        ]
        result = list(messages_col().aggregate(pipeline))
        if result:
            r = result[0]
            return {"total": r.get("total", 0), "incoming": r.get("incoming", 0),
                    "outgoing": r.get("outgoing", 0), "commands": r.get("commands", 0)}
        return {"total": 0, "incoming": 0, "outgoing": 0, "commands": 0}