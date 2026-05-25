from sim.tool.base_tool import BaseTool
from sim.tool.tool_type import ToolType

class LightSignalTool(BaseTool):
    def __init__(self):
        super().__init__("light_signal", ToolType.LIGHT_SIGNAL)

    def get_description(self):
        return "인벤토리에 '마른 나뭇가지'와 '부싯돌'이 있을 때 '정찰 언덕'에서 실행 가능. 거대한 연기 봉화를 피워 제인과 함께 구조를 요청함."

    def get_params(self):
        return ''

    def execute(self, params, agent, world_system_manager):
        inv = agent.get_inventory()
        current_location = agent.location_delegate.get_current_location()
        branches = inv.get_pack("마른 나뭇가지")
        flint = inv.get_pack("부싯돌")

        if current_location != "정찰 언덕":
            world_system_manager.log_world_event(f"{agent.name}가 구조 봉화를 피우려 했으나, 구조용 신호 화대가 있는 '정찰 언덕'이 아닙니다.")
            return
        
        if len(branches) > 0 and len(flint) > 0:
            world_system_manager.log_world_event(
                f"[구조 신호 격발] {agent.name}가 수집한 마른 나뭇가지를 화대에 쌓고 부싯돌을 튕겨 거대한 연기 봉화를 피워 올림. "
                f"섬의 안개를 뚫고 솟구친 검은 연기를 포착한 원양 수송선에 의해, {agent.name}와 어린 JAIN은 기적적으로 함께 구조됨."
            )
            world_system_manager.log_system_event("CRITICAL_END: SIMULATION_SUCCESS_SIGNAL_ESCAPE")
            world_system_manager.event_trigger.stop()
        else:
            world_system_manager.log_world_event(f"{agent.name}가 구조 봉화를 피우려 했으나 필요한 자원(마른 나뭇가지 혹은 부싯돌)이 부족함")