class BaseObject:
    def __init__(self, id, type):
        self.id = id
        self.type = type
        self.objects = []

        # 소유 속성
        self.is_owned = False
        self.owner_id = None

        # 일반 속성
        self.name = ""
        self.description = ""
        
        # 물리 속성
        self.color = ""
        self.volume = None
        self.size = None
        self.weight = None
        self.durability = None

        # 기능적 속성
        self.is_breakable = False
        self.is_interactive = False

        # 위치 속성
        self.location = None