from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid

class LocalizedContent(BaseModel):
    ko: Optional[str] = Field(None, description="Korean content")
    en: Optional[str] = Field(None, description="English content")
    ja: Optional[str] = Field(None, description="Japanese content")

    class Config:
        extra = 'forbid'  # This prevents additional fields


class LanguageProficiency(BaseModel):
    language_code: str
    proficiency: str
    preference_order: int = Field(ge=1)

class PersonalityTrait(BaseModel):
    trait: str
    score: float = Field(ge=0.0, le=1.0)

class Interest(BaseModel):
    topic: str
    level: str

class CharacterBase(BaseModel):
    version: str
    names: LocalizedContent
    gender: str
    age: int = Field(ge=0, le=150)
    personality_traits: List[PersonalityTrait]
    interests: List[Interest]
    occupation: LocalizedContent
    background: LocalizedContent
    appearance_seed: str
    appearance_description: LocalizedContent
    relationship_status: Optional[str] = None
    languages: List[LanguageProficiency]
    conversation_style: LocalizedContent
    communication_preferences: Dict[str, str]
    backstory: LocalizedContent
    goals: LocalizedContent
    quirks: LocalizedContent
    emotional_intelligence: float = Field(ge=0.0, le=1.0)
    cultural_sensitivity: float = Field(ge=0.0, le=1.0)
    relationship_progression_pace: str
    conflict_resolution_style: str
    interaction_prompts: Dict[str, LocalizedContent]
    character_prompt: str
    response_generation_parameters: Dict[str, float]
    is_public: bool = False

class CharacterCreate(CharacterBase):
    pass

class CharacterUpdate(BaseModel):
    version: Optional[str] = None
    names: Optional[LocalizedContent] = None
    gender: Optional[str] = None
    age: Optional[int] = Field(None, ge=0, le=150)
    personality_traits: Optional[List[PersonalityTrait]] = None
    interests: Optional[List[Interest]] = None
    occupation: Optional[LocalizedContent] = None
    background: Optional[LocalizedContent] = None
    appearance_seed: Optional[str] = None
    appearance_description: Optional[LocalizedContent] = None
    relationship_status: Optional[str] = None
    languages: Optional[List[LanguageProficiency]] = None
    conversation_style: Optional[LocalizedContent] = None
    communication_preferences: Optional[Dict[str, str]] = None
    backstory: Optional[LocalizedContent] = None
    goals: Optional[LocalizedContent] = None
    quirks: Optional[LocalizedContent] = None
    emotional_intelligence: Optional[float] = Field(None, ge=0.0, le=1.0)
    cultural_sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    relationship_progression_pace: Optional[str] = None
    conflict_resolution_style: Optional[str] = None
    interaction_prompts: Optional[Dict[str, LocalizedContent]] = None
    character_prompt: Optional[str] = None
    response_generation_parameters: Optional[Dict[str, float]] = None
    is_public: Optional[bool] = None

class CharacterInDB(CharacterBase):
    id: uuid.UUID
    creator_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CharacterProfile(CharacterBase):
    id: uuid.UUID
    creator_id: str

    class Config:
        from_attributes = True