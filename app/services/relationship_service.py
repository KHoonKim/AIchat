import os
from app.models.relationship import RelationshipCreate, RelationshipType, RelationshipUpdate, RelationshipInDB
from supabase import create_client, Client
from fastapi import HTTPException


supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")


supabase: Client = create_client(supabase_url, supabase_key)


class RelationshipService:
    async def get_relationship(self, character_id: str, user_id: str) -> RelationshipInDB:
        response = supabase.table("relationships").select("*").eq("character_id", character_id).eq("user_id", user_id).execute()
        if response.data:
            return RelationshipInDB(**response.data[0])
        raise HTTPException(status_code=404, detail="Relationship not found")

    async def create_relationship(self, relationship: RelationshipCreate) -> RelationshipInDB:
        response = supabase.table("relationships").insert(relationship.dict()).execute()
        if response.data:
            return RelationshipInDB(**response.data[0])
        raise HTTPException(status_code=400, detail="Failed to create relationship")

    async def update_relationship(self, character_id: str, user_id: str, relationship: RelationshipUpdate) -> RelationshipInDB:
        response = supabase.table("relationships").update(relationship.dict(exclude_unset=True)).eq("character_id", character_id).eq("user_id", user_id).execute()
        if response.data:
            return RelationshipInDB(**response.data[0])
        raise HTTPException(status_code=400, detail="Failed to update relationship")

    async def update_affinity(self, character_id: str, user_id: str, affinity_change: float):
        relationship = await self.get_relationship(character_id, user_id)
        new_affinity = max(-100, min(100, relationship.affinity + affinity_change))
        await self.update_relationship(character_id, user_id, RelationshipUpdate(affinity=new_affinity))

    async def update_affinity_and_relationship_type(self, character_id: str, user_id: str, affinity_change: float):
        relationship = await self.get_relationship(character_id, user_id)
        new_affinity = max(-100, min(100, relationship.affinity + affinity_change))
        new_relationship_type = self.get_relationship_type(new_affinity)
        await self.update_relationship(
            character_id,
            user_id,
            RelationshipUpdate(affinity=new_affinity, relationship_type=new_relationship_type)
        )
    
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