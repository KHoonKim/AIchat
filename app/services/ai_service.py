import asyncio
import os
from typing import Any, Dict, List
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

import openai
from pinecone import Pinecone, ServerlessSpec


class AIService:
    def __init__(self):
        openai.api_key = os.environ.get('OPENAI_API_KEY')

        # Pinecone 초기화
        self.pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
        
        # 인덱스 이름 가져오기
        index_name = os.environ.get("PINECONE_INDEX_NAME")

        # 인덱스가 존재하지 않으면 생성
        if index_name not in self.pc.list_indexes().names():
            self.pc.create_index(
                name=index_name,
                dimension=1536,  # OpenAI의 text-embedding-ada-002 모델의 출력 차원
                metric='cosine',
                spec=ServerlessSpec(cloud=os.environ.get("PINECONE_CLOUD", "aws"), 
                                    region=os.environ.get("PINECONE_REGION", "us-west-2"))
            )
        
        # 인덱스 연결
        self.index = self.pc.Index(index_name)

    def vectorize_text(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환하는 메서드"""
        response = openai.Embedding.create(
            input=text,
            model="text-embedding-ada-002"
        )
        embedding = response['data'][0]['embedding']
        return embedding

    def store_vector(self, id: str, vector: List[float], metadata: Dict[str, Any]):
        """벡터를 Pinecone에 저장하는 메서드"""
        self.index.upsert(vectors=[(id, vector, metadata)])

    async def store_vector_async(self, id: str, vector: List[float], metadata: Dict[str, Any]):
        """벡터를 Pinecone에 비동기적으로 저장하는 메서드"""
        # 비동기 실행을 위해 run_in_executor 사용
        await asyncio.get_event_loop().run_in_executor(
            None, self.store_vector, id, vector, metadata
        )

    
    def search_similar_vectors(self, vector: List[float], conversation_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        특정 대화 내에서 유사한 벡터를 검색하는 메서드
        
        :param vector: 검색할 벡터
        :param conversation_id: 검색 대상 대화 ID
        :param top_k: 반환할 최대 결과 수
        :return: 유사한 벡터들의 정보 (ID, 점수, 메타데이터)
        """
        results = self.index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            filter={"conversation_id": conversation_id}
        )
        return results['matches']
    
    async def generate_response(self, context: str) -> str:
        """
        주어진 컨텍스트를 바탕으로 AI 응답을 생성하는 메서드
        
        :param context: 대화 컨텍스트
        :return: 생성된 AI 응답
        """
        # TODO: 실제 AI 모델을 사용하여 응답 생성
        # 이 부분은 실제 AI 모델 API를 호출하는 로직으로 대체되어야 합니다.
        return f"AI response based on context: {context[:50]}..."  # 예시 응답
