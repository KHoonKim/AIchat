import logging
import os
from typing import List
from fastapi import APIRouter, HTTPException
from app.models.conversation import ConversationCreate, ConversationUpdate, ConversationProfile, MessageCreate, MessageProfile
from app.models.user import UserProfile as User
from supabase import create_client, Client
import uuid


router = APIRouter()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

supabase: Client = create_client(supabase_url, supabase_key)

async def create_conversation(conversation: ConversationCreate, current_user: User) -> ConversationProfile:
    try:
        # create_conversation 함수 내부
        conversation_data = conversation.model_dump()
        conversation_data['user_id'] = str(current_user.id)  # UUID를 문자열로 변환
        conversation_data['character_id'] = str(conversation.character_id)  # UUID를 문자열로 변환


        
        response = supabase.table("conversations").insert(conversation_data).execute()
        if response.data:
            return ConversationProfile(**response.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to create conversation")
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def get_conversation(conversation_id: str, current_user: User) -> ConversationProfile:
    try:
        response = supabase.table("conversations").select("*").eq("id", conversation_id).execute()
        if response.data:
            conversation = response.data[0]
            if conversation['user_id'] == current_user.id:
                return ConversationProfile(**conversation)
            else:
                raise HTTPException(status_code=403, detail="You don't have permission to access this conversation")
        else:
            raise HTTPException(status_code=404, detail="Conversation not found")
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def update_conversation(conversation_id: str, conversation: ConversationUpdate, current_user: User) -> ConversationProfile:
    try:
        existing_conversation = await get_conversation(conversation_id, current_user)
        if existing_conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You don't have permission to update this conversation")
        
        update_data = conversation.model_dump(exclude_unset=True)
        
        response = supabase.table("conversations").update(update_data).eq("id", conversation_id).execute()
        if response.data:
            return ConversationProfile(**response.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to update conversation")
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def delete_conversation(conversation_id: str, current_user: User):
    try:
        existing_conversation = await get_conversation(conversation_id, current_user)
        if existing_conversation.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You don't have permission to delete this conversation")
        
        response = supabase.table("conversations").delete().eq("id", conversation_id).execute()
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to delete conversation")
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def list_conversations(current_user: User) -> List[ConversationProfile]:
    try:
        response = supabase.table("conversations").select("*").eq("user_id", current_user.id).execute()
        
        if response.data:
            return [ConversationProfile(**conversation) for conversation in response.data]
        else:
            return []
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def create_message(conversation_id: str, message: MessageCreate, current_user: User) -> MessageProfile:
    try:
        # Ensure the conversation belongs to the current user
        await get_conversation(conversation_id, current_user)
        
        message_data = message.model_dump()
        message_data['conversation_id'] = conversation_id
        
        response = supabase.table("messages").insert(message_data).execute()
        if response.data:
            return MessageProfile(**response.data[0])
        else:
            raise HTTPException(status_code=400, detail="Failed to create message")
    except Exception as e:
        logger.error(f"Error creating message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

async def list_messages(conversation_id: str, current_user: User) -> List[MessageProfile]:
    try:
        # Ensure the conversation belongs to the current user
        await get_conversation(conversation_id, current_user)
        
        response = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
        
        if response.data:
            return [MessageProfile(**message) for message in response.data]
        else:
            return []
    except Exception as e:
        logger.error(f"Error listing messages: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    

async def get_message(message_id: str, current_user: User) -> MessageProfile:
    try:
        response = supabase.table("messages").select("*").eq("id", message_id).execute()
        if response.data:
            message = response.data[0]
            # 메시지에 대한 권한 확인
            conversation = await get_conversation(message['conversation_id'], current_user)
            if conversation.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="You don't have permission to access this message")
            return MessageProfile(**message)
        else:
            raise HTTPException(status_code=404, detail="Message not found")
    except Exception as e:
        logger.error(f"Error getting message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))