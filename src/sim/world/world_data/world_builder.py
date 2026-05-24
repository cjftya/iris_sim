class WorldBuilder:
    def __init__(self, world_type):
        self._world_type = world_type
        self._agents = []
        self._objects = []

    def _add_agent(self, agent):
        self._agents.append(agent)

    def _add_object(self, obj):
        self._objects.append(obj)

    def get_world_type(self):
        return self._world_type

    def _create_agents(self, world_system_manager):
        pass

    def _create_objects(self, world_system_manager):
        pass

    def build(self, world_system_manager):
        self._create_agents(world_system_manager)
        self._create_objects(world_system_manager)
        return self._agents, self._objects

    