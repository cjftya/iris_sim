from sim.object_meta.base_object import BaseObject
from sim.object_meta.object_type import ObjectType

class SpaceObject(BaseObject):
    def __init__(self, name, detail=None, parent=None):
        super().__init__(name, detail, ObjectType.SPACE, parent)