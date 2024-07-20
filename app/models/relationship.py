from enum import Enum
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class RelationshipType(Enum):
    ENEMY = "enemy"
    RIVAL = "rival"
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    LOVER = "lover"
    SPOUSE = "spouse"

class RelationshipBase(BaseModel):
    user_id: str
    character_id: str
    affinity: float = 0
    relationship_type: RelationshipType = RelationshipType.STRANGER
    nickname: Optional[str] = None
    last_interaction: datetime = datetime.now(datetime.timezone.utc)

class RelationshipCreate(RelationshipBase):
    pass

class RelationshipUpdate(BaseModel):
    affinity: Optional[float] = None
    relationship_type: Optional[RelationshipType] = None
    nickname: Optional[str] = None
    last_interaction: Optional[datetime] = None

class RelationshipInDB(RelationshipBase):
    id: str

    class Config:
        orm_mode = True