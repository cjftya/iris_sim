from sim.tool.base_tool import BaseTool
from sim.world.event_trigger import ThinkEventType
from sim.tool.tool_type import ToolType

class InspectTool(BaseTool):
    def __init__(self):
        super().__init__("inspect", ToolType.INSPECT)

    def get_description(self):
        return "내 눈앞에 식별된 특정 사물이 '무엇'인지 전혀 모르거나 궁금할때 사용."

    def get_params(self):
        return '{"object_id": "Available Objects 중 하나"}'

    def execute(self, params, agent, world_system_manager):
        reason = params.get('reason', None)
        object_id = params.get('object_id')
        target_object = world_system_manager.object_manager.get_object(object_id)
        if not target_object:
            world_system_manager.log_system_event("skip function call: inspect, target object null")
            return

        context = f"[{reason}] 라는 이유로, 나는 {target_object.name}를 자세히 관찰함. 관찰한 결과: {target_object.detail}"
        agent.push_think_event(ThinkEventType.INSPECT, context, agent.name)
        world_system_manager.log_world_event(f"{agent.name}가 {target_object.name}을 관찰.")
        