from typing import List

from fastapi import APIRouter, Depends

from app.models.character import (CharacterCreate, CharacterProfile,
                                  CharacterUpdate)
from app.models.user import UserProfile as User
from app.services.auth_service import get_current_user
from app.services.character_service import (create_character, delete_character,
                                            get_character, list_characters,
                                            update_character)

router = APIRouter()

@router.post("/characters", response_model=CharacterProfile)
async def create_character_route(character: CharacterCreate, current_user: User = Depends(get_current_user)):
    return await create_character(character, current_user)

@router.get("/characters/{character_id}", response_model=CharacterProfile)
async def get_character_route(character_id: str, current_user: User = Depends(get_current_user)):
    return await get_character(character_id, current_user)

@router.put("/characters/{character_id}", response_model=CharacterProfile)
async def update_character_route(character_id: str, character: CharacterUpdate, current_user: User = Depends(get_current_user)):
    return await update_character(character_id, character, current_user)

@router.delete("/characters/{character_id}")
async def delete_character_route(character_id: str, current_user: User = Depends(get_current_user)):
    await delete_character(character_id, current_user)
    return {"message": "Character deleted successfully"}

@router.get("/characters", response_model=List[CharacterProfile])
async def list_characters_route(current_user: User = Depends(get_current_user)):
    return await list_characters(current_user)