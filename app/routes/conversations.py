from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.conversation import ConversationCreate, ConversationUpdate, ConversationProfile, MessageCreate, MessageProfile
from app.services.auth_service import get_current_user
from app.services.conversation_service import (
    create_conversation, get_conversation, update_conversation, delete_conversation, list_conversations,
    create_message, get_message, list_messages
)
from app.models.user import UserProfile as User

router = APIRouter()

@router.post("/conversations", response_model=ConversationProfile)
async def create_conversation_route(conversation: ConversationCreate, current_user: User = Depends(get_current_user)):
    return await create_conversation(conversation, current_user)

@router.get("/conversations/{conversation_id}", response_model=ConversationProfile)
async def get_conversation_route(conversation_id: str, current_user: User = Depends(get_current_user)):
    return await get_conversation(conversation_id, current_user)

@router.put("/conversations/{conversation_id}", response_model=ConversationProfile)
async def update_conversation_route(conversation_id: str, conversation: ConversationUpdate, current_user: User = Depends(get_current_user)):
    return await update_conversation(conversation_id, conversation, current_user)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation_route(conversation_id: str, current_user: User = Depends(get_current_user)):
    await delete_conversation(conversation_id, current_user)
    return {"message": "Conversation deleted successfully"}

@router.get("/conversations", response_model=List[ConversationProfile])
async def list_conversations_route(current_user: User = Depends(get_current_user)):
    return await list_conversations(current_user)

@router.post("/conversations/{conversation_id}/messages", response_model=MessageProfile)
async def create_message_route(conversation_id: str, message: MessageCreate, current_user: User = Depends(get_current_user)):
    return await create_message(conversation_id, message, current_user)

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageProfile])
async def list_messages_route(conversation_id: str, current_user: User = Depends(get_current_user)):
    return await list_messages(conversation_id, current_user)

@router.get("/conversations/{conversation_id}/messages/{message_id}", response_model=MessageProfile)
async def get_message_route(conversation_id: str, message_id: str, current_user: User = Depends(get_current_user)):
    return await get_message(message_id, current_user)