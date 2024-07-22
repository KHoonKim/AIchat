# # models/scenario.py

# from pydantic import BaseModel
# from typing import List, Optional
# from enum import Enum
# from datetime import datetime

# class ScenarioTriggerType(Enum):
#     """시나리오 트리거 유형을 정의하는 열거형 클래스"""
#     AFFINITY = "affinity"  # 호감도 기반 트리거
#     TIME = "time"  # 시간 기반 트리거
#     EVENT = "event"  # 특정 이벤트 기반 트리거

# class ScenarioStep(BaseModel):
#     """시나리오의 각 단계를 표현하는 모델"""
#     step_id: str
#     content: str
#     image_url: Optional[str] = None  # 해당 단계와 관련된 이미지 URL (선택적)

# class Scenario(BaseModel):
#     """시나리오의 전체 구조를 표현하는 모델"""
#     id: str
#     character_id: str
#     title: str
#     description: str
#     trigger_type: ScenarioTriggerType
#     trigger_value: float  # 예: 호감도 60 또는 7일 후 등
#     steps: List[ScenarioStep]
#     created_at: datetime
#     updated_at: datetime

# class ScenarioProgress(BaseModel):
#     """사용자별 시나리오 진행 상황을 표현하는 모델"""
#     id: str
#     user_id: str
#     scenario_id: str
#     current_step: int
#     started_at: datetime
#     completed_at: Optional[datetime] = None
#     is_completed: bool = False

# class ScenarioCreate(BaseModel):
#     """시나리오 생성을 위한 입력 모델"""
#     character_id: str
#     title: str
#     description: str
#     trigger_type: ScenarioTriggerType
#     trigger_value: float
#     steps: List[ScenarioStep]

# class ScenarioUpdate(BaseModel):
#     """시나리오 업데이트를 위한 입력 모델"""
#     title: Optional[str] = None
#     description: Optional[str] = None
#     trigger_type: Optional[ScenarioTriggerType] = None
#     trigger_value: Optional[float] = None
#     steps: Optional[List[ScenarioStep]] = None