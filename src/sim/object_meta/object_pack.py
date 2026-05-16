class ObjectPack:
    def __init__(self):
        self.object_ids = set()

    def add_object(self, obj_id):
        self.object_ids.add(obj_id)

    def remove_object(self, obj_id):
        self.object_ids.remove(obj_id)

    def get_object_ids(self):
        return list(self.object_ids)

    def get_object_count(self):
        return len(self.object_ids)

    def clear_objects(self):
        self.object_ids.clear()