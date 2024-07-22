from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.models.conversation import ConversationCreate, ConversationUpdate, ConversationProfile, MessageCreate, MessageProfile
from app.services.auth_service import get_current_user
from app.services.conversation_service import ConversationService
from app.models.user import UserProfile as User
from app.models.relationship import RelationshipType, UserCharacterInteractionUpdate

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
    return await conversation_service.create_message_and_respond(conversation_id, message, current_user)

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageProfile])
async def list_messages_route(conversation_id: str, current_user: User = Depends(get_current_user)):
    return await conversation_service.list_messages(conversation_id, current_user)

@router.get("/conversations/{conversation_id}/messages/{message_id}", response_model=MessageProfile)
async def get_message_route(conversation_id: str, message_id: str, current_user: User = Depends(get_current_user)):
    return await conversation_service.get_message(message_id, current_user)

@router.post("/conversations/{conversation_id}/summarize")
async def summarize_conversation_route(conversation_id: str, current_user: User = Depends(get_current_user)):
    summary = await conversation_service.summarize_conversation(conversation_id, current_user)
    return {"summary": summary}

@router.get("/conversations/{conversation_id}/similar-messages")
async def get_similar_messages_route(
    conversation_id: str, 
    message_content: str = Query(..., description="Content of the message to find similar ones"),
    top_k: int = Query(5, description="Number of similar messages to return"),
    current_user: User = Depends(get_current_user)
):
    similar_messages = await conversation_service.get_similar_messages(conversation_id, message_content, top_k)
    return {"similar_messages": similar_messages}

@router.get("/conversations/{conversation_id}/message-count")
async def get_message_count_route(conversation_id: str, current_user: User = Depends(get_current_user)):
    count = await conversation_service.get_message_count(conversation_id)
    return {"message_count": count}

@router.put("/conversations/{conversation_id}/nickname")
async def update_nickname_route(
    conversation_id: str,
    nickname: str = Query(..., description="New nickname for the user"),
    current_user: User = Depends(get_current_user)
):
    conversation = await conversation_service.get_conversation(conversation_id, current_user)
    await conversation_service.relationship_service.update_interaction(
        str(conversation.character_id),
        str(current_user.id),
        UserCharacterInteractionUpdate(nickname=nickname)
    )
    return {"message": "Nickname updated successfully"}

@router.put("/conversations/{conversation_id}/relationship-type")
async def update_relationship_type_route(
    conversation_id: str,
    relationship_type: RelationshipType,
    current_user: User = Depends(get_current_user)
):
    conversation = await conversation_service.get_conversation(conversation_id, current_user)
    await conversation_service.relationship_service.update_interaction(
        str(conversation.character_id),
        str(current_user.id),
        relationship_type
    )
    return {"message": "Relationship type updated successfully"}