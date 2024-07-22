from datetime import datetime, timezone
import os
import json
from app.models.relationship import UserCharacterInteractionUpdate, RelationshipType, UserCharacterInteractionCreate, UserCharacterInteractionInDB
from supabase import create_client, Client
from fastapi import HTTPException
from app.config import redis_client



supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")


supabase: Client = create_client(supabase_url, supabase_key)


class RelationshipService:
    def __init__(self):
        self.redis_client = redis_client

    async def get_interaction(self, character_id: str, user_id: str) -> UserCharacterInteractionInDB:
        # Redis에서 먼저 확인
        cached_interaction = self.redis_client.get(f"interaction:{character_id}:{user_id}")
        if cached_interaction:
            return UserCharacterInteractionInDB(**json.loads(cached_interaction))
        
        # Redis에 없으면 데이터베이스에서 조회
        response = supabase.table("user_character_interactions").select("*").eq("character_id", character_id).eq("user_id", user_id).execute()
        if response.data:
            interaction = UserCharacterInteractionInDB(**response.data[0])
            # Redis에 캐시 저장
            self.redis_client.setex(f"interaction:{character_id}:{user_id}", 3600, json.dumps(interaction.model_dump()))  # 1시간 동안 캐시
            return interaction
        raise HTTPException(status_code=404, detail="Interaction not found")


    async def create_interaction(self, interaction: UserCharacterInteractionCreate) -> UserCharacterInteractionInDB:
        response = supabase.table("user_character_interactions").insert(interaction.model_dump()).execute()
        if response.data:
            created_interaction = UserCharacterInteractionInDB(**response.data[0])
            # Redis에 캐시 저장
            self.redis_client.setex(
                f"interaction:{created_interaction.character_id}:{created_interaction.user_id}",
                3600,
                json.dumps(created_interaction.model_dump())
            )
            return created_interaction
        raise HTTPException(status_code=400, detail="Failed to create interaction")

    async def update_interaction(self, character_id: str, user_id: str, interaction: UserCharacterInteractionUpdate) -> UserCharacterInteractionInDB:
        update_data = interaction.model_dump(exclude_unset=True)
        update_data['last_interaction'] = datetime.now(timezone.utc)
        response = supabase.table("user_character_interactions").update(update_data).eq("character_id", character_id).eq("user_id", user_id).execute()
        if response.data:
            updated_interaction = UserCharacterInteractionInDB(**response.data[0])
            # Redis 캐시 업데이트
            self.redis_client.setex(f"interaction:{character_id}:{user_id}", 3600, json.dumps(updated_interaction.model_dump()))
            return updated_interaction
        raise HTTPException(status_code=400, detail="Failed to update interaction")


    async def update_affinity(self, character_id: str, user_id: str, affinity_change: float):
        interaction = await self.get_interaction(character_id, user_id)
        new_affinity = max(-100, min(100, interaction.affinity + affinity_change))
        new_relationship_type = self.get_relationship_type(new_affinity)
        updated_interaction = await self.update_interaction(
            character_id,
            user_id,
            UserCharacterInteractionUpdate(
                affinity=new_affinity, 
                relationship_type=new_relationship_type,
                interaction_count=interaction.interaction_count + 1
            )
        )
        # Redis 캐시 업데이트
        self.redis_client.setex(f"interaction:{character_id}:{user_id}", 3600, json.dumps(updated_interaction.model_dump()))
    
    def get_affinity_level(self, affinity: float) -> str:
        if affinity <= -91:
            return "극도로 부정적"
        elif affinity <= -71:
            return "매우 부정적"
        elif affinity <= -41:
            return "부정적"
        elif affinity <= -11:
            return "약간 부정적"
        elif affinity <= 10:
            return "중립"
        elif affinity <= 40:
            return "긍정적"
        elif affinity <= 60:
            return "매우 긍정적"
        elif affinity <= 70:
            return "사랑에 빠짐"
        elif affinity <= 90:
            return "깊이 사랑에 빠짐"
        else:
            return "극도로 사랑함"
    
    def get_relationship_type(self, affinity: float) -> RelationshipType:
        if affinity <= -91:
            return RelationshipType.ENEMY
        elif affinity <= -51:
            return RelationshipType.RIVAL
        elif affinity <= 10:
            return RelationshipType.STRANGER
        elif affinity <= 20:
            return RelationshipType.ACQUAINTANCE
        elif affinity <= 30:
            return RelationshipType.FRIEND
        elif affinity <= 50:
            return RelationshipType.CLOSE_FRIEND
        elif affinity <= 70:
            return RelationshipType.LOVER
        elif affinity <= 100:
            return RelationshipType.SPOUSE
        else:
            raise ValueError("Affinity value out of bounds")
    
    async def update_custom_traits(self, character_id: str, user_id: str, custom_traits: dict):
        updated_interaction = await self.update_interaction(
            character_id,
            user_id,
            UserCharacterInteractionUpdate(custom_traits=custom_traits)
        )
        # Redis 캐시 업데이트
        self.redis_client.setex(f"interaction:{character_id}:{user_id}", 3600, json.dumps(updated_interaction.model_dump()))

    async def update_conversation_history(self, character_id: str, user_id: str, conversation_history: dict):
        updated_interaction = await self.update_interaction(
            character_id,
            user_id,
            UserCharacterInteractionUpdate(conversation_history=conversation_history)
        )
        # Redis 캐시 업데이트
        self.redis_client.setex(f"interaction:{character_id}:{user_id}", 3600, json.dumps(updated_interaction.model_dump()))