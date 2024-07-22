# # services/scenario_service.py

# import asyncio
# from app.models.scenario import Scenario, ScenarioProgress, ScenarioCreate, ScenarioUpdate, ScenarioStep
# from app.services.relationship_service import RelationshipService
# from datetime import datetime
# from typing import List, Optional
# from app.config import supabase_client  # Supabase 클라이언트 설정이 필요합니다

# async def db_get_scenario(scenario_id: str) -> Optional[Scenario]:
#     """
#     데이터베이스에서 특정 시나리오를 조회합니다.
#     시나리오의 단계 정보도 함께 가져옵니다.
#     """
#     result = await supabase_client.table('scenarios').select('*, scenario_steps(*)').eq('id', scenario_id).execute()
#     if result.data:
#         scenario_data = result.data[0]
#         steps = [ScenarioStep(**step) for step in scenario_data.pop('scenario_steps')]
#         return Scenario(**scenario_data, steps=steps)
#     return None

# async def db_create_scenario(scenario: ScenarioCreate) -> Scenario:
#     """
#     새로운 시나리오를 데이터베이스에 생성합니다.
#     시나리오 기본 정보와 각 단계를 별도의 테이블에 저장합니다.
#     """
#     scenario_data = scenario.model_dump(exclude={'steps'})
#     result = await supabase_client.table('scenarios').insert(scenario_data).execute()
#     created_scenario = result.data[0]
    
#     steps_data = [{"scenario_id": created_scenario['id'], "step_order": i, **step.model_dump()} 
#                   for i, step in enumerate(scenario.steps)]
#     await supabase_client.table('scenario_steps').insert(steps_data).execute()
    
#     return await db_get_scenario(created_scenario['id'])

# async def db_update_scenario(scenario_id: str, scenario_update: ScenarioUpdate) -> Scenario:
#     """
#     기존 시나리오를 업데이트합니다.
#     시나리오 기본 정보와 단계 정보를 모두 업데이트합니다.
#     """
#     update_data = scenario_update.model_dump(exclude_unset=True)
#     steps = update_data.pop('steps', None)
    
#     result = await supabase_client.table('scenarios').update(update_data).eq('id', scenario_id).execute()
    
#     if steps is not None:
#         # 기존 단계를 삭제하고 새로운 단계를 추가합니다.
#         await supabase_client.table('scenario_steps').delete().eq('scenario_id', scenario_id).execute()
#         steps_data = [{"scenario_id": scenario_id, "step_order": i, **step.model_dump()} 
#                       for i, step in enumerate(steps)]
#         await supabase_client.table('scenario_steps').insert(steps_data).execute()
    
#     return await db_get_scenario(scenario_id)

# async def db_delete_scenario(scenario_id: str) -> bool:
#     """
#     특정 시나리오를 데이터베이스에서 삭제합니다.
#     관련된 단계 정보도 함께 삭제됩니다 (CASCADE 설정에 의해).
#     """
#     result = await supabase_client.table('scenarios').delete().eq('id', scenario_id).execute()
#     return len(result.data) > 0

# async def db_get_scenario_progress(user_id: str, scenario_id: str) -> Optional[ScenarioProgress]:
#     """
#     특정 사용자의 특정 시나리오 진행 상황을 조회합니다.
#     """
#     result = await supabase_client.table('scenario_progress').select('*').eq('user_id', user_id).eq('scenario_id', scenario_id).execute()
#     if result.data:
#         return ScenarioProgress(**result.data[0])
#     return None

# async def db_update_scenario_progress(progress: ScenarioProgress) -> ScenarioProgress:
#     """
#     시나리오 진행 상황을 업데이트하거나 새로 생성합니다.
#     """
#     progress_data = progress.model_dump()
#     result = await supabase_client.table('scenario_progress').upsert(progress_data).execute()
#     return ScenarioProgress(**result.data[0])

# async def create_scenario(scenario: ScenarioCreate) -> Scenario:
#     """시나리오를 생성하고 데이터베이스에 저장합니다."""
#     return await db_create_scenario(scenario)

# async def get_scenario(scenario_id: str) -> Optional[Scenario]:
#     """특정 ID의 시나리오를 조회합니다."""
#     return await db_get_scenario(scenario_id)

# async def update_scenario(scenario_id: str, scenario_update: ScenarioUpdate) -> Scenario:
#     """시나리오 정보를 업데이트합니다."""
#     return await db_update_scenario(scenario_id, scenario_update)

# async def delete_scenario(scenario_id: str) -> bool:
#     """시나리오를 삭제합니다."""
#     return await db_delete_scenario(scenario_id)

# async def check_scenario_trigger(user_id: str, character_id: str) -> Optional[Scenario]:
#     """
#     현재 사용자와 캐릭터의 관계 상태를 확인하고,
#     트리거될 수 있는 시나리오가 있는지 확인합니다.
#     """
#     relationship_service = RelationshipService()
#     relationship = await relationship_service.get_interaction(user_id, character_id)

    
#     result = await supabase_client.table('scenarios').select('*').eq('character_id', character_id).execute()
#     scenarios = [Scenario(**scenario) for scenario in result.data]
    
#     # 비동기로 여러 시나리오를 동시에 체크합니다.
#     async def check_scenario(scenario):
#         if scenario.trigger_type == "affinity" and relationship.affinity >= scenario.trigger_value:
#             return scenario
#         return None

#     checked_scenarios = await asyncio.gather(*[check_scenario(scenario) for scenario in scenarios])
#     triggered_scenarios = [s for s in checked_scenarios if s is not None]
    
#     return triggered_scenarios[0] if triggered_scenarios else None

# async def start_scenario(user_id: str, scenario_id: str) -> ScenarioProgress:
#     """
#     특정 사용자에 대해 시나리오를 시작합니다.
#     시나리오 진행 상황을 생성하고 저장합니다.
#     """
#     scenario = await get_scenario(scenario_id)
#     if not scenario:
#         raise ValueError("Scenario not found")
    
#     progress = ScenarioProgress(
#         id=f"{user_id}_{scenario_id}",
#         user_id=user_id,
#         scenario_id=scenario_id,
#         current_step=0,
#         started_at=datetime.now(),
#         is_completed=False
#     )
    
#     return await db_update_scenario_progress(progress)

# async def progress_scenario(user_id: str, scenario_id: str) -> ScenarioProgress:
#     """
#     시나리오를 한 단계 진행시킵니다.
#     마지막 단계에 도달하면 시나리오를 완료 상태로 표시합니다.
#     """
#     progress = await db_get_scenario_progress(user_id, scenario_id)
#     if not progress:
#         raise ValueError("Scenario progress not found")
    
#     scenario = await get_scenario(scenario_id)
#     if not scenario:
#         raise ValueError("Scenario not found")
    
#     if progress.current_step < len(scenario.steps) - 1:
#         progress.current_step += 1
#     else:
#         progress.is_completed = True
#         progress.completed_at = datetime.now()
    
#     return await db_update_scenario_progress(progress)

# async def get_scenario_message(scenario_id: str, step: int) -> str:
#     """
#     특정 시나리오의 특정 단계 메시지를 반환합니다.
#     """
#     scenario = await get_scenario(scenario_id)
#     if not scenario or step >= len(scenario.steps):
#         raise ValueError("Invalid scenario or step")
    
#     return scenario.steps[step].content

# # 비동기 최적화를 위한 추가 함수
# async def get_all_scenarios_for_character(character_id: str) -> List[Scenario]:
#     """
#     특정 캐릭터의 모든 시나리오를 조회합니다.
#     """
#     result = await supabase_client.table('scenarios').select('*, scenario_steps(*)').eq('character_id', character_id).execute()
#     scenarios = []
#     for scenario_data in result.data:
#         steps = [ScenarioStep(**step) for step in scenario_data.pop('scenario_steps')]
#         scenarios.append(Scenario(**scenario_data, steps=steps))
#     return scenarios

# async def bulk_update_scenario_progress(progresses: List[ScenarioProgress]) -> List[ScenarioProgress]:
#     """
#     여러 시나리오 진행 상황을 한 번에 업데이트합니다.
#     """
#     progress_data = [progress.model_dump() for progress in progresses]
#     result = await supabase_client.table('scenario_progress').upsert(progress_data).execute()
#     return [ScenarioProgress(**data) for data in result.data]