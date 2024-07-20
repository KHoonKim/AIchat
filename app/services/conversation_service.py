from datetime import datetime, timezone
import logging
import os
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from app.models.conversation import ConversationCreate, ConversationUpdate, ConversationProfile, MessageCreate, MessageProfile
from app.models.user import UserProfile as User
from supabase import create_client, Client
from app.services.ai_service import AIService
import uuid
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import HumanMessage, AIMessage
from langchain.llms import OpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from app.services.relationship_service import RelationshipService
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from app.models.relationship import RelationshipCreate, RelationshipUpdate, RelationshipInDB



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
        self.llm = OpenAI(temperature=0)  # OpenAI 모델 초기화
        self.summarize_chain = load_summarize_chain(self.llm, chain_type="map_reduce")
        self.ai_service = AIService()

        self.relationship_service = RelationshipService()
        self.llm = ChatOpenAI(temperature=0.7)
        self.prompt_template = PromptTemplate(
            input_variables=["context", "recent_messages", "summary", "similar_messages", "affinity", "nickname"],
            template="""
            당신은 AI 연인입니다. 다음 정보를 바탕으로 대화에 참여하세요:
            
            대화 컨텍스트: {context}
            최근 메시지들: {recent_messages}
            대화 요약: {summary}
            유사한 메시지들: {similar_messages}
            호감도 (태도 참고용): {affinity}
            사용자가 부르는 호칭: {nickname}
            
            위 정보를 참고하여 자연스럽고 개성 있는 답변을 생성하세요. 호감도에 따라 태도를 적절히 조절하세요.
            """
        )
        self.llm_chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

        self.relationship_service = RelationshipService()
        self.llm = ChatOpenAI(temperature=0.7)
        self.affinity_prompt = PromptTemplate(
            input_variables=["summary"],
            template="""
            다음은 대화의 요약입니다:
            {summary}
            
            이 대화 요약을 바탕으로, AI 캐릭터의 사용자에 대한 호감도 변화를 평가해주세요.
            호감도 변화를 -5에서 5 사이의 숫자로 표현해주세요. 
            -5는 AI 캐릭터가 사용자에 대해 매우 부정적인 변화를 느낌, 0은 변화 없음, 5는 매우 긍정적인 변화를 느낌을 의미합니다.
            
            호감도 변화 점수:
            """
        )
        self.affinity_chain = LLMChain(llm=self.llm, prompt=self.affinity_prompt)



    async def summarize_conversation(self, conversation_id: str, current_user: User) -> str:
        # 대화 내용 가져오기
        messages = await self.list_messages(conversation_id, current_user)
        
        # 최근 10개의 메시지만 선택
        recent_messages = messages[-10:]
        
        # 메시지를 Document 객체로 변환
        docs = [Document(page_content=msg.content) for msg in recent_messages]
        
        # 요약 생성
        summary = self.summarize_chain.run(docs)
        
        # 요약 결과 저장
        await self.save_summary(conversation_id, summary)
        
        # AI 캐릭터의 호감도 변화 계산
        affinity_change = await self.calculate_affinity_change(summary)
        
        # 관계 정보 업데이트
        conversation = await self.get_conversation(conversation_id, current_user)
        await self.relationship_service.update_affinity(str(conversation.character_id), str(current_user.id), affinity_change)
        
        return summary

    async def save_summary(self, conversation_id: str, summary: str):
        """
        생성된 요약을 저장하는 메서드
        
        :param conversation_id: 대화 ID
        :param summary: 저장할 요약 내용
        """
        try:
            # Supabase에 요약 저장
            response = supabase.table("conversation_summaries").insert({
                "conversation_id": conversation_id,
                "summary": summary,
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            
            if not response.data:
                raise HTTPException(status_code=400, detail="Failed to save summary")
        except Exception as e:
            logger.error(f"Error saving summary: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        
    async def create_message_and_respond(self, conversation_id: str, message: MessageCreate, current_user: User) -> MessageProfile:
        created_message = await self.create_message(conversation_id, message, current_user)
        
        if message.sender == "user":
            conversation = await self.get_conversation(conversation_id, current_user)
            ai_response = await self.generate_ai_response(conversation_id, str(current_user.id), str(conversation.character_id))
            
            ai_message = MessageCreate(sender="character", content=ai_response)
            await self.create_message(conversation_id, ai_message, current_user)
        
        return created_message

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
            
            # 메시지 생성 후 메시지 개수 확인
            message_count = await self.get_message_count(conversation_id)
            # 메시지 개수가 10의 배수일 때 요약 생성
            if message_count % 10 == 0:
                await self.summarize_conversation(conversation_id, current_user)

            # 메시지 내용 벡터화
            vector = self.ai_service.vectorize_text(message.content)
            message_data['embedding'] = vector

            
            # Supabase에 메시지 저장 (벡터 포함)
            response = supabase.table("messages").insert(message_data).execute()
            
            if response.data:
                created_message = MessageProfile(**response.data[0])
                
                # Pinecone에 벡터 저장
                await self.ai_service.store_vector_async(
                    id=str(created_message.id),
                    vector=vector,
                    metadata={
                        "conversation_id": conversation_id,
                        "content": message.content,
                        "created_at": created_message.created_at.isoformat()
                    }
                )
                
                return created_message
            else:
                raise HTTPException(status_code=400, detail="Failed to create message")
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

    
    async def get_similar_messages(self, conversation_id: str, message_content: str, top_k: int = 5) -> List[MessageProfile]:
        """
        특정 대화 내에서 유사한 메시지를 검색하는 메서드
        
        :param conversation_id: 검색 대상 대화 ID
        :param message_content: 검색할 메시지 내용
        :param top_k: 반환할 최대 결과 수
        :return: 유사한 메시지들의 정보
        """
        vector = self.ai_service.vectorize_text(message_content)
        similar_vectors = self.ai_service.search_similar_vectors(vector, conversation_id, top_k)
        
        similar_messages = []
        for match in similar_vectors:
            message_id = match['id']
            message = await self.get_message(message_id, None)  # 여기서 None은 임시로 사용. 실제로는 적절한 권한 체크가 필요합니다.
            similar_messages.append(message)
        
        return similar_messages
    
    async def get_message_count(self, conversation_id: str) -> int:
        """
        특정 대화의 메시지 개수를 반환하는 메서드
        
        :param conversation_id: 대화 ID
        :return: 메시지 개수
        """
        try:
            response = supabase.table("messages").select("id", count="exact").eq("conversation_id", conversation_id).execute()
            return response.count
        except Exception as e:
            logger.error(f"Error getting message count: {str(e)}")
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

    async def generate_ai_response(self, conversation_id: str, user_id: str, character_id: str) -> str:
        recent_messages = await self.get_recent_messages(conversation_id, 10)
        summary = await self.get_conversation_summary(conversation_id)
        similar_messages = await self.get_similar_messages(conversation_id, recent_messages[-1].content, 3)
        relationship = await self.relationship_service.get_relationship(user_id, character_id)
        affinity_level = self.relationship_service.get_affinity_level(relationship.affinity)
        
        prompt_template = PromptTemplate(
            input_variables=["recent_messages", "summary", "similar_messages", "affinity_level", "relationship_type", "nickname"],
            template="""
            당신은 AI 캐릭터입니다. 다음 정보를 바탕으로 사용자와의 대화에 참여하세요:
            
            최근 메시지들:
            {recent_messages}
            
            대화 요약:
            {summary}
            
            유사한 과거 메시지들:
            {similar_messages}
            
            사용자에 대한 호감도: {affinity_level}
            사용자와의 관계: {relationship_type}
            사용자의 별명: {nickname}
            
            위 정보를 참고하여 자연스럽고 개성 있는 답변을 생성하세요. 
            호감도와 관계 유형에 맞는 적절한 어조와 친밀도를 사용하세요.
            이전 대화 내용과 일관성을 유지하면서, 대화를 발전시키는 답변을 제공하세요.
            """
        )

        llm = ChatOpenAI(temperature=0.7)
        llm_chain = LLMChain(llm=llm, prompt=prompt_template)
        
        ai_response = llm_chain.run(
            recent_messages=self.format_messages(recent_messages),
            summary=summary,
            similar_messages=self.format_messages(similar_messages),
            affinity_level=affinity_level,
            relationship_type=relationship.relationship_type.value,
            nickname=relationship.nickname or "사용자"
        )
        
        return ai_response

    def format_messages(self, messages: List[MessageProfile]) -> str:
        return "\n".join([f"{msg.sender}: {msg.content}" for msg in messages])


    async def update_affinity(self, conversation_id: str, user_id: str, character_id: str, message_content: str):
        # 감정 분석 또는 키워드 기반 호감도 계산 로직
        affinity_change = self.calculate_affinity_change(message_content)
        
        relationship = await self.relationship_service.get_relationship(user_id, character_id)
        new_affinity = max(-100, min(100, relationship.affinity + affinity_change))
        
        await self.relationship_service.update_relationship(
            user_id, 
            character_id, 
            RelationshipUpdate(affinity=new_affinity, last_interaction=datetime.datetime.now(timezone.utc))
        )
    
    def calculate_affinity_change(self, message_content: str) -> float:
        # 간단한 키워드 기반 호감도 변화 계산 (실제 구현 시 더 복잡한 로직 사용 가능)
        positive_keywords = ["좋아", "감사", "행복", "사랑"]
        negative_keywords = ["싫어", "짜증", "화나", "미워"]
        
        affinity_change = 0
        for word in positive_keywords:
            if word in message_content:
                affinity_change += 0.5
        for word in negative_keywords:
            if word in message_content:
                affinity_change -= 0.5
        
        return affinity_change

# 기존 함수들은 ConversationService 클래스의 메서드로 변환되었으므로 삭제