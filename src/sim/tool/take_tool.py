from sim.tool.base_tool import BaseTool
from sim.tool.tool_type import ToolType

class TakeTool(BaseTool):
    def __init__(self):
        super().__init__("take", ToolType.TAKE)

    def get_description(self):
        return "바닥이나 구역에 놓인 물체를 내 소유(인벤토리)로 획득."

    def get_params(self):
        return '{"object_id": "Available Objects 중 하나"}'

    def execute(self, params, agent, world_system_manager):
        object_id = params.get('object_id')
        target_object = world_system_manager.object_manager.get_object_by_id(object_id)
        if target_object:
            name_key = target_object.name
            poped_object = world_system_manager.object_manager.pop_object(name_key)
            poped_object.parent = None
            agent.get_inventory().add_object(poped_object)

            world_system_manager.log_world_event(f"{agent.name}가 {name_key}을 획득.")
        else:
            world_system_manager.log_world_event(f"{agent.name}가 {object_id}을 획득할 수 없음.")