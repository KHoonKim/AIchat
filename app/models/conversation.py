from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Literal
from datetime import datetime
import uuid

class ConversationBase(BaseModel):
    # user_id: uuid.UUID
    # character_id: uuid.UUID
    user_id: str = Field(..., description="User ID as string")
    character_id: str = Field(..., description="Character ID as string")
    context: Optional[Dict] = Field(default_factory=dict)
    state: Optional[Dict] = Field(default_factory=dict)

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    context: Optional[Dict] = None
    state: Optional[Dict] = None

class ConversationInDB(ConversationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationProfile(ConversationInDB):
    pass

class MessageBase(BaseModel):
    conversation_id: uuid.UUID
    sender_type: Literal['user', 'character']
    content: List[Dict]
    metadata: Optional[Dict] = Field(default_factory=dict)

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    content: Optional[List[Dict]] = None
    metadata: Optional[Dict] = None

class MessageInDB(MessageBase):
    id: uuid.UUID
    created_at: datetime
    embedding: Optional[List[float]] = None

    class Config:
        from_attributes = True

class MessageProfile(MessageBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True