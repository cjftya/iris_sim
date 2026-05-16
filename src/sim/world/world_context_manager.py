from sim.object_meta.object_manager import ObjectManager
from sim.agent_meta.agent_manager import AgentManager
from sim.world.world_object_creator import WorldObjectCreator
from sim.world.weather_engine import WeatherEngine
from sim.world.time_engine import TimeEngine
from sim.sim_agent.lim import Lim

class WorldContextManager:
    def __init__(self):
        self.agent_manager = AgentManager()
        self.object_manager = ObjectManager()
        self.world_object_creator = WorldObjectCreator()
        self.weather_engine = WeatherEngine()
        self.time_engine = TimeEngine()

        # agents
        self.agent_lim = Lim(world_context_manager=self)

    def start(self):
        objects = self.world_object_creator.create_lim_world()
        for obj in objects:
            self.object_manager.add_object(obj)

        self.agent_manager.add_agent(self.agent_lim)
        for agent in self.agent_manager.get_all_agents():
            agent.start()

    def stop(self):
        for agent in self.agent_manager.get_all_agents():
            agent.stop()
        self.agent_manager.clear_agents()
        self.object_manager.clear_objects()

    def tick(self):
        self.weather_engine.tick()
        self.time_engine.tick()

        # TODO: add logic
        # 1. update world state
        # 2. random event update (external energy intake)
        # 3. trigger thinking
        self.agent_lim.run()
    
    def get_context(self):
        return f"""\
{self.time_engine.get_context()}\n
{self.weather_engine.get_context()}"""


        