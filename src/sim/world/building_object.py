from sim.world.base_object import BaseObject
from sim.world.object_type import ObjectType

class BuildingObject(BaseObject):
    def __init__(self, id):
        super().__init__(id, ObjectType.BUILDING)