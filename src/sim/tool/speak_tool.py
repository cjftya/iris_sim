from sim.tool.base_tool import BaseTool
from sim.world.event_trigger import ThinkEventType
from sim.tool.tool_type import ToolType

class SpeakTool(BaseTool):
    def __init__(self):
        super().__init__("speak", ToolType.SPEAK)

    def get_description(self):
        return "주관적 의도 전달 및 소통."

    def get_params(self):
        return '{"agent_name": "Available Participants 중 한명", "message": "대화할 내용"}'

    def execute(self, params, agent, world_system_manager):
        target_agent_name = params.get('agent_name')
        target_agent = world_system_manager.agent_manager.get_agent_by_name(target_agent_name)
        message = params.get('message', '')
        if target_agent:
            target_agent.push_think_event(ThinkEventType.SPEAK, message, agent.name)
            world_system_manager.log_world_event(f"{agent.name}가 {target_agent.name}에게 말을 걸었음.")
        else:
            world_system_manager.log_world_event(f"{agent.name}가 {target_agent_name}에게 말을 걸 수 없음.")
        