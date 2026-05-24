from sim.tool.base_tool import BaseTool
from sim.tool.tool_type import ToolType

class BuildRaftTool(BaseTool):
    def __init__(self):
        super().__init__("build_raft", ToolType.BUILD_RAFT)

    def get_description(self):
        return "인벤토리에 '단단한 통나무'와 '질긴 덩굴'이 수집되어 있을 때만 실행 가능함. 거친 바다를 돌파할 탈출용 뗏목을 제작하여 능동적 탈출을 감행함."

    def get_params(self):
        return ''

    def execute(self, params, agent, world_system_manager):
        inv = agent.get_inventory()
        logs = inv.find_item("단단한 통나무")
        vines = inv.find_item("질긴 덩굴")
        
        if logs and vines:
            world_system_manager.log_world_event(f"🔥 [역대급 엔딩: 능동적 생존 탈출] {agent.name}가 야생에서 수집한 통나무와 덩굴을 엮어 견고한 탈출용 뗏목을 조립해 냈습니다! 거친 집사광 파도를 뚫고 망망대해로 나아가 고향으로 복귀하는 데 대성공했습니다! 시뮬레이션을 중지합니다.")
            world_system_manager.log_system_event("CRITICAL_END: SIMULATION_SUCCESS_RAFT_ESCAPE")
            # 시뮬레이터를 멈추기 위해 인터럽트 플래그 강제 주입
            world_system_manager.event_trigger.turns_since_last_thought = -99999
        else:
            world_system_manager.log_world_event(f"{agent.name}가 뗏목 조립을 시도했으나 자원(단단한 통나무 혹은 질긴 덩굴)이 가방에 부족합니다.")