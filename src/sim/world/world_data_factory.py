from sim.world.world_data.world_type import WorldType
from sim.world.world_data.lim_world_builder import LimWorldBuilder
from sim.world.world_data.castway_world_builder import CastAwayWorldBuilder

class WorldDataFactory:
    def __init__(self):
        pass

    def get_world_data(self, world_type, world_system_manager):
        if world_type == WorldType.LIM_SIM:
            return LimWorldBuilder().build(world_system_manager)
        elif world_type == WorldType.CAST_AWAY_SIM:
            return CastAwayWorldBuilder().build(world_system_manager)

        return None, None