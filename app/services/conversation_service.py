import logging
import os
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from app.models.conversation import ConversationCreate, ConversationUpdate, ConversationProfile, MessageCreate, MessageProfile
from app.models.user import UserProfile as User
from supabase import create_client, Client
import uuid
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage
import json

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env file")

supabase: Client = create_client(supabase_url, supabase_key)

class ConversationContextManager: # 대화 컨텍스트 관리자
    def __init__(self, window_size: int = 10): # window_size: 대화 기록 윈도우 크기
        self.memory = ConversationBufferWindowMemory(k=window_size) # 대화 기록 메모리
        self.relationship_info = {} # 관계 정보
        self.current_scenario = None # 현재 시나리오

    def add_message(self, role: str, content: str): # role: 메시지 발신자 역할, content: 메시지 내용
        if role == 'human':
            self.memory.chat_memory.add_message(HumanMessage(content=content))
        elif role == 'ai':
            self.memory.chat_memory.add_message(AIMessage(content=content))

    def get_conversation_history(self) -> List[Dict[str, str]]:
        return [{"role": msg.type, "content": msg.content} for msg in self.memory.chat_memory.messages]

    def update_relationship_info(self, affinity: float, interaction_count: int):
        self.relationship_info.update({
            "affinity": affinity,
            "interaction_count": interaction_count
        })

    def set_current_scenario(self, scenario: Dict[str, any]):
        self.current_scenario = scenario

    def get_formatted_context(self) -> str:
        context = {
            "conversation_history": self.get_conversation_history(),
            "relationship_info": self.relationship_info,
            "current_scenario": self.current_scenario
        }
        return json.dumps(context, ensure_ascii=False, indent=2)

    def clear_context(self):
        self.memory.clear()
        self.relationship_info = {}
        self.current_scenario = None

class ConversationService:
    def __init__(self):
        self.context_manager = ConversationContextManager()

    async def create_conversation(self, conversation: ConversationCreate, current_user: User) -> ConversationProfile:
        try:
            conversation_data = conversation.model_dump()
            conversation_data['user_id'] = str(current_user.id)
            conversation_data['character_id'] = str(conversation.character_id)
            
            response = supabase.table("conversations").insert(conversation_data).execute()
            if response.data:
                self.context_manager.clear_context()
                return ConversationProfile(**response.data[0])
            else:
                raise HTTPException(status_code=400, detail="Failed to create conversation")
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def get_conversation(self, conversation_id: str, current_user: User) -> ConversationProfile:
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

    async def update_conversation(self, conversation_id: str, conversation: ConversationUpdate, current_user: User) -> ConversationProfile:
        try:
            existing_conversation = await self.get_conversation(conversation_id, current_user)
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

    async def delete_conversation(self, conversation_id: str, current_user: User):
        try:
            existing_conversation = await self.get_conversation(conversation_id, current_user)
            if existing_conversation.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="You don't have permission to delete this conversation")
            
            response = supabase.table("conversations").delete().eq("id", conversation_id).execute()
            if not response.data:
                raise HTTPException(status_code=400, detail="Failed to delete conversation")
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def list_conversations(self, current_user: User) -> List[ConversationProfile]:
        try:
            response = supabase.table("conversations").select("*").eq("user_id", current_user.id).execute()
            
            if response.data:
                return [ConversationProfile(**conversation) for conversation in response.data]
            else:
                return []
        except Exception as e:
            logger.error(f"Error listing conversations: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def create_message(self, conversation_id: str, message: MessageCreate, current_user: User) -> MessageProfile:
        try:
            await self.get_conversation(conversation_id, current_user)
            
            message_data = message.model_dump()
            message_data['conversation_id'] = conversation_id
            
            self.context_manager.add_message("human" if message.sender == "user" else "ai", message.content)
            
            response = supabase.table("messages").insert(message_data).execute()
            if response.data:
                return MessageProfile(**response.data[0])
            else:
                raise HTTPException(status_code=400, detail="Failed to create message")
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def list_messages(self, conversation_id: str, current_user: User) -> List[MessageProfile]:
        try:
            await self.get_conversation(conversation_id, current_user)
            
            response = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("created_at").execute()
            
            if response.data:
                return [MessageProfile(**message) for message in response.data]
            else:
                return []
        except Exception as e:
            logger.error(f"Error listing messages: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def get_message(self, message_id: str, current_user: User) -> MessageProfile:
        try:
            response = supabase.table("messages").select("*").eq("id", message_id).execute()
            if response.data:
                message = response.data[0]
                conversation = await self.get_conversation(message['conversation_id'], current_user)
                if conversation.user_id != current_user.id:
                    raise HTTPException(status_code=403, detail="You don't have permission to access this message")
                return MessageProfile(**message)
            else:
                raise HTTPException(status_code=404, detail="Message not found")
        except Exception as e:
            logger.error(f"Error getting message: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def update_relationship(self, user_id: str, character_id: str, affinity: float, interaction_count: int):
        try:
            self.context_manager.update_relationship_info(affinity, interaction_count)
            # 여기에 데이터베이스 업데이트 로직 추가
        except Exception as e:
            logger.error(f"Error updating relationship: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def set_scenario(self, scenario_id: str):
        try:
            scenario = await self.get_scenario_from_db(scenario_id)
            self.context_manager.set_current_scenario(scenario)
        except Exception as e:
            logger.error(f"Error setting scenario: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    async def get_scenario_from_db(self, scenario_id: str):
        # 데이터베이스에서 시나리오 정보를 가져오는 로직 구현
        # 예시:
        response = supabase.table("scenarios").select("*").eq("id", scenario_id).execute()
        if response.data:
            return response.data[0]
        else:
            raise HTTPException(status_code=404, detail="Scenario not found")

    async def generate_ai_response(self, conversation_id: str, current_user: User) -> str:
        # AI 응답 생성 로직
        # 이 부분은 별도의 AI 서비스와 연동하여 구현해야 합니다.
        context = self.context_manager.get_formatted_context()
        # AI 서비스 호출 및 응답 생성
        ai_response = "이 부분은 실제 AI 모델의 응답으로 대체되어야 합니다."
        
        # 생성된 응답을 컨텍스트에 추가
        self.context_manager.add_message("ai", ai_response)
        
        return ai_response

# 기존 함수들은 ConversationService 클래스의 메서드로 변환되었으므로 삭제