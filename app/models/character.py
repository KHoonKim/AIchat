# models/character.py

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List, Dict, Literal
from datetime import datetime
import uuid

class LocalizedContent(BaseModel):
    content: Dict[str, str]

class LanguageProficiency(BaseModel):
    language_code: str
    proficiency: Literal['native', 'fluent', 'intermediate', 'beginner']
    preference_order: int = Field(ge=1)

    @field_validator('language_code')
    @classmethod
    def validate_language_code(cls, v):
        if len(v) != 2:
            raise ValueError('Language code must be 2 characters long')
        return v.lower()

class PersonalityTrait(BaseModel):
    trait: str
    score: float = Field(ge=0.0, le=1.0)

class Interest(BaseModel):
    topic: str
    level: Literal['high', 'medium', 'low']

class Character(BaseModel):
    id: Optional[uuid.UUID] = None
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
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    relationship_status: Optional[str] = None
    languages: List[LanguageProficiency]
    conversation_style: LocalizedContent
    communication_preferences: Dict[str, str]
    backstory: LocalizedContent
    goals: LocalizedContent
    quirks: LocalizedContent
    emotional_intelligence: float = Field(ge=0.0, le=1.0)
    cultural_sensitivity: float = Field(ge=0.0, le=1.0)
    relationship_progression_pace: Literal['slow', 'moderate', 'fast']
    conflict_resolution_style: str
    interaction_prompts: Dict[str, LocalizedContent]
    character_prompt: str
    response_generation_parameters: Dict[str, float]

    model_config = ConfigDict(from_attributes=True)

class CharacterCreate(BaseModel):
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
    languages: List[LanguageProficiency]
    conversation_style: LocalizedContent
    communication_preferences: Dict[str, str]
    backstory: LocalizedContent
    goals: LocalizedContent
    quirks: LocalizedContent
    emotional_intelligence: float = Field(ge=0.0, le=1.0)
    cultural_sensitivity: float = Field(ge=0.0, le=1.0)
    relationship_progression_pace: Literal['slow', 'moderate', 'fast']
    conflict_resolution_style: str
    interaction_prompts: Dict[str, LocalizedContent]
    character_prompt: str
    response_generation_parameters: Dict[str, float]

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
    relationship_progression_pace: Optional[Literal['slow', 'moderate', 'fast']] = None
    conflict_resolution_style: Optional[str] = None
    interaction_prompts: Optional[Dict[str, LocalizedContent]] = None
    character_prompt: Optional[str] = None
    response_generation_parameters: Optional[Dict[str, float]] = None

class CharacterInDB(Character):
    pass

class CharacterProfile(BaseModel):
    id: uuid.UUID
    names: LocalizedContent
    gender: str
    age: int
    occupation: LocalizedContent
    appearance_description: LocalizedContent

    model_config = ConfigDict(from_attributes=True)

class UserCharacterInteraction(BaseModel):
    id: Optional[uuid.UUID] = None
    user_id: uuid.UUID
    character_id: uuid.UUID
    interaction_count: int = Field(default=0, ge=0)
    last_interaction_date: datetime = Field(default_factory=datetime.now)
    conversation_memory: Optional[int] = Field(None, ge=0)
    learning_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    relationship_level: Optional[int] = Field(None, ge=0)
    custom_traits: Optional[Dict[str, float]] = None
    conversation_history: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)