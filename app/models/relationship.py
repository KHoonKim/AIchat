from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class RelationshipType(Enum):
    ENEMY = "enemy"
    RIVAL = "rival"
    STRANGER = "stranger"
    ACQUAINTANCE = "acquaintance"
    FRIEND = "friend"
    CLOSE_FRIEND = "close_friend"
    LOVER = "lover"
    SPOUSE = "spouse"

class UserCharacterInteractionBase(BaseModel):
    user_id: str
    character_id: str
    affinity: float = 0
    relationship_type: RelationshipType = RelationshipType.STRANGER
    nickname: Optional[str] = None
    last_interaction: datetime = datetime.now(timezone.utc)
    interaction_count: int = 0
    conversation_memory: int = 0
    learning_rate: float = 0.0
    custom_traits: dict = {}
    conversation_history: dict = {}

class UserCharacterInteractionCreate(UserCharacterInteractionBase):
    pass

class UserCharacterInteractionUpdate(BaseModel):
    affinity: Optional[float] = None
    relationship_type: Optional[RelationshipType] = None
    nickname: Optional[str] = None
    last_interaction: Optional[datetime] = None
    interaction_count: Optional[int] = None
    conversation_memory: Optional[int] = None
    learning_rate: Optional[float] = None
    custom_traits: Optional[dict] = None
    conversation_history: Optional[dict] = None
    
class UserCharacterInteractionInDB(UserCharacterInteractionBase):
    id: str

    class Config:
        orm_mode = True

