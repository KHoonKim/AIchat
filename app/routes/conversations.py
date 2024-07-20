from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models.conversation import ConversationCreate, ConversationUpdate, ConversationProfile, MessageCreate, MessageProfile
from app.services.auth_service import get_current_user
from app.services.conversation_service import ConversationService
from app.models.user import UserProfile as User

router = APIRouter()
conversation_service = ConversationService()

@router.post("/conversations", response_model=ConversationProfile)
async def create_conversation_route(conversation: ConversationCreate, current_user: User = Depends(get_current_user)):
    return await conversation_service.create_conversation(conversation, current_user)

@router.get("/conversations/{conversation_id}", response_model=ConversationProfile)
async def get_conversation_route(conversation_id: str, current_user: User = Depends(get_current_user)):
    return await conversation_service.get_conversation(conversation_id, current_user)

@router.put("/conversations/{conversation_id}", response_model=ConversationProfile)
async def update_conversation_route(conversation_id: str, conversation: ConversationUpdate, current_user: User = Depends(get_current_user)):
    return await conversation_service.update_conversation(conversation_id, conversation, current_user)

@router.delete("/conversations/{conversation_id}")
async def delete_conversation_route(conversation_id: str, current_user: User = Depends(get_current_user)):
    await conversation_service.delete_conversation(conversation_id, current_user)
    return {"message": "Conversation deleted successfully"}

@router.get("/conversations", response_model=List[ConversationProfile])
async def list_conversations_route(current_user: User = Depends(get_current_user)):
    return await conversation_service.list_conversations(current_user)

@router.post("/conversations/{conversation_id}/messages", response_model=MessageProfile)
async def create_message_route(conversation_id: str, message: MessageCreate, current_user: User = Depends(get_current_user)):
    return await conversation_service.create_message(conversation_id, message, current_user)

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageProfile])
async def list_messages_route(conversation_id: str, current_user: User = Depends(get_current_user)):
    return await conversation_service.list_messages(conversation_id, current_user)

@router.get("/conversations/{conversation_id}/messages/{message_id}", response_model=MessageProfile)
async def get_message_route(conversation_id: str, message_id: str, current_user: User = Depends(get_current_user)):
    return await conversation_service.get_message(message_id, current_user)

@router.post("/conversations/{conversation_id}/ai-response")
async def generate_ai_response_route(conversation_id: str, current_user: User = Depends(get_current_user)):
    ai_response = await conversation_service.generate_ai_response(conversation_id, current_user)
    return {"ai_response": ai_response}

@router.post("/conversations/{conversation_id}/update-relationship")
async def update_relationship_route(conversation_id: str, affinity: float, interaction_count: int, current_user: User = Depends(get_current_user)):
    conversation = await conversation_service.get_conversation(conversation_id, current_user)
    await conversation_service.update_relationship(str(current_user.id), str(conversation.character_id), affinity, interaction_count)
    return {"message": "Relationship updated successfully"}

@router.post("/conversations/{conversation_id}/set-scenario")
async def set_scenario_route(conversation_id: str, scenario_id: str, current_user: User = Depends(get_current_user)):
    await conversation_service.get_conversation(conversation_id, current_user)  # Ensure the conversation exists and belongs to the user
    await conversation_service.set_scenario(scenario_id)
    return {"message": "Scenario set successfully"}