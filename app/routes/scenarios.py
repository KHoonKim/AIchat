# # routes/scenarios.py

# from fastapi import APIRouter, HTTPException, Depends
# from typing import List
# from app.models.scenario import ScenarioCreate, ScenarioUpdate, Scenario, ScenarioProgress
# from app.services import scenario_service
# from app.models.user import UserProfile as User
# from app.dependencies import get_current_user

# router = APIRouter()

# @router.post("/scenarios", response_model=Scenario)
# async def create_scenario(scenario: ScenarioCreate, current_user: User = Depends(get_current_user)):
#     """
#     새로운 시나리오를 생성합니다.
#     """
#     return await scenario_service.create_scenario(scenario)

# @router.get("/scenarios/{scenario_id}", response_model=Scenario)
# async def get_scenario(scenario_id: str, current_user: User = Depends(get_current_user)):
#     """
#     특정 시나리오의 정보를 조회합니다.
#     """
#     scenario = await scenario_service.get_scenario(scenario_id)
#     if not scenario:
#         raise HTTPException(status_code=404, detail="Scenario not found")
#     return scenario

# @router.put("/scenarios/{scenario_id}", response_model=Scenario)
# async def update_scenario(scenario_id: str, scenario_update: ScenarioUpdate, current_user: User = Depends(get_current_user)):
#     """
#     시나리오 정보를 업데이트합니다.
#     """
#     updated_scenario = await scenario_service.update_scenario(scenario_id, scenario_update)
#     if not updated_scenario:
#         raise HTTPException(status_code=404, detail="Scenario not found")
#     return updated_scenario

# @router.delete("/scenarios/{scenario_id}", response_model=bool)
# async def delete_scenario(scenario_id: str, current_user: User = Depends(get_current_user)):
#     """
#     시나리오를 삭제합니다.
#     """
#     deleted = await scenario_service.delete_scenario(scenario_id)
#     if not deleted:
#         raise HTTPException(status_code=404, detail="Scenario not found")
#     return True

# @router.post("/scenarios/{scenario_id}/start", response_model=ScenarioProgress)
# async def start_scenario(scenario_id: str, current_user: User = Depends(get_current_user)):
#     """
#     특정 사용자에 대해 시나리오를 시작합니다.
#     """
#     try:
#         progress = await scenario_service.start_scenario(str(current_user.id), scenario_id)
#         return progress
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

# @router.post("/scenarios/{scenario_id}/progress", response_model=ScenarioProgress)
# async def progress_scenario(scenario_id: str, current_user: User = Depends(get_current_user)):
#     """
#     시나리오를 한 단계 진행시킵니다.
#     """
#     try:
#         progress = await scenario_service.progress_scenario(str(current_user.id), scenario_id)
#         return progress
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))

# @router.get("/scenarios/check_trigger", response_model=Scenario)
# async def check_scenario_trigger(character_id: str, current_user: User = Depends(get_current_user)):
#     """
#     현재 상태에서 트리거될 수 있는 시나리오를 확인합니다.
#     """
#     scenario = await scenario_service.check_scenario_trigger(str(current_user.id), character_id)
#     if not scenario:
#         raise HTTPException(status_code=404, detail="No scenario triggered")
#     return scenario

# @router.get("/scenarios", response_model=List[Scenario])
# async def list_scenarios(character_id: str, current_user: User = Depends(get_current_user)):
#     """
#     특정 캐릭터의 모든 시나리오를 조회합니다.
#     """
#     scenarios = await scenario_service.get_all_scenarios_for_character(character_id)
#     return scenarios

# @router.get("/scenarios/{scenario_id}/progress", response_model=ScenarioProgress)
# async def get_scenario_progress(scenario_id: str, current_user: User = Depends(get_current_user)):
#     """
#     특정 시나리오의 현재 진행 상황을 조회합니다.
#     """
#     progress = await scenario_service.get_scenario_progress(str(current_user.id), scenario_id)
#     if not progress:
#         raise HTTPException(status_code=404, detail="Scenario progress not found")
#     return progress