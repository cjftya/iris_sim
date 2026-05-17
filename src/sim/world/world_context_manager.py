from sim.object_meta.object_manager import ObjectManager
from sim.agent_meta.agent_manager import AgentManager
from sim.world.world_object_creator import WorldObjectCreator
from sim.world.weather_engine import WeatherEngine
from sim.world.time_engine import TimeEngine
from sim.sim_agent.lim import Lim
from sim.world.event_emitter import EventEmitter

class WorldContextManager:
    def __init__(self):
        self.agent_manager = AgentManager()
        self.object_manager = ObjectManager()
        self.world_object_creator = WorldObjectCreator()
        self.weather_engine = WeatherEngine()
        self.time_engine = TimeEngine()
        self.event_emitter = EventEmitter()

        # agents
        self.agent_manager.add_agent(Lim(world_context_manager=self))
        self.agents = self.agent_manager.get_agents()
        
    def start(self):
        objects = self.world_object_creator.create_lim_world()
        for obj in objects:
            self.object_manager.add_object(obj)

        for agent in self.agents:
            agent.start()

    def stop(self):
        for agent in self.agents:
            agent.stop()
        self.agent_manager.clear_agents()
        self.object_manager.clear_objects()

    def tick(self):
        # 1. update world time
        self.time_engine.tick()

        # 2. update weather
        self.weather_engine.tick(self.time_engine.time_scale, self.time_engine.season)

        # 3. update events
        self.event_emitter.tick()

        # 4. trigger thinking
        # 5. update agents
        for agent in self.agents:
            agent.tick(self.time_engine.time_scale)
    
    def get_context(self):
        return f"""\
{self.time_engine.get_context()}\n
{self.weather_engine.get_context()}"""


        