from sim.object_meta.base_object import BaseObject
from sim.object_meta.object_type import ObjectType

class BuildingObject(BaseObject):
    def __init__(self, name, detail=None):
        super().__init__(name, detail, ObjectType.BUILDING)