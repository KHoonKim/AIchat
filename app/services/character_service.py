# services/character_service.py

import logging
import os
from typing import List
from fastapi import APIRouter, HTTPException
from app.models.character import CharacterCreate, CharacterUpdate, CharacterProfile
from app.models.user import UserProfile as User
from supabase import create_client, Client

router = APIRouter()


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")


supabase: Client = create_client(supabase_url, supabase_key)
def is_admin(user: User) -> bool:
    return user.is_admin




async def create_character(character: CharacterCreate, current_user: User) -> CharacterProfile:
    try:
        character_data = character.model_dump()
        character_data['creator_id'] = current_user.id
        
        # Convert LocalizedContent fields to JSON
        for field in ['names', 'occupation', 'background', 'appearance_description']:
            if field in character_data:
                character_data[field] = character_data[field].dict()
        
        response = supabase.table("characters").insert(character_data).execute()
        if response.data:
            return CharacterProfile(**response.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to create character")
    except Exception as e:
        logger.error(f"Error creating character: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def get_character(character_id: str, current_user: User) -> CharacterProfile:
    try:
        response = supabase.table("characters").select("*").eq("id", character_id).execute()
        if response.data:
            character = response.data[0]
            if character['creator_id'] == current_user.id or is_admin(current_user):
                return CharacterProfile(**character)
            else:
                raise HTTPException(status_code=403, detail="You don't have permission to access this character")
        else:
            raise HTTPException(status_code=404, detail="Character not found")
    except Exception as e:
        logger.error(f"Error getting character: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def update_character(character_id: str, character: CharacterUpdate, current_user: User) -> CharacterProfile:
    try:
        existing_character = await get_character(character_id, current_user)
        if existing_character.creator_id != current_user.id and not is_admin(current_user):
            raise HTTPException(status_code=403, detail="You don't have permission to update this character")
        
        update_data = character.model_dump(exclude_unset=True)
        
        # Convert LocalizedContent fields to JSON
        for field in ['names', 'occupation', 'background', 'appearance_description']:
            if field in update_data:
                update_data[field] = update_data[field].dict()
        
        response = supabase.table("characters").update(update_data).eq("id", character_id).execute()
        if response.data:
            return CharacterProfile(**response.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to update character")
    except Exception as e:
        logger.error(f"Error updating character: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def delete_character(character_id: str, current_user: User):
    try:
        existing_character = await get_character(character_id, current_user)
        if existing_character.creator_id != current_user.id and not is_admin(current_user):
            raise HTTPException(status_code=403, detail="You don't have permission to delete this character")
        
        response = supabase.table("characters").delete().eq("id", character_id).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to delete character")
    except Exception as e:
        logger.error(f"Error deleting character: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def list_characters(current_user: User) -> List[CharacterProfile]:
    try:
        if is_admin(current_user):
            response = supabase.table("characters").select("*").execute()
        else:
            response = supabase.table("characters").select("*").or_(f"creator_id.eq.{current_user.id},is_public.eq.true").execute()
        
        if response.data:
            return [CharacterProfile(**character) for character in response.data]
        else:
            return []
    except Exception as e:
        logger.error(f"Error listing characters: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
