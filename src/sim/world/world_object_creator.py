from sim.object_meta.space_object import SpaceObject
from sim.object_meta.building_object import BuildingObject
from sim.object_meta.item_object import ItemObject

class WorldObjectCreator:
    def __init__(self):
        pass

    def create_lim_world(self):
        objects = []

        # LIM의 집
        lim_house = BuildingObject(
            name="LIM의 집",
            detail="주변에 아무도 없고 어둡고 음산한 기운이 도는 집."
        )
        objects.append(lim_house)

        sleeping_room = SpaceObject("자는방", "어두운 침실, 따로 가구는 없고 침대만 덩그러니 있다.")
        sleeping_room.child_objects.add_object(ItemObject("거울", "자신의 얼굴을 비추는 거울"))
        sleeping_room.child_objects.add_object(ItemObject("침대", "잠을 잘 수 있는 침대, 하지만 누군가 지켜보는 듯한 기분이 든다."))

        living_room = SpaceObject("거실", "비교적 깔끔한 거실, 어딘가 서늘한 기운이 감돈다")
        living_room.child_objects.add_object(ItemObject("쇼파", "누군가 앉았던 흔적이 있는 쇼파"))
        living_room.child_objects.add_object(ItemObject("가족사진", "행복했던 날의 추억이 담긴 가족사진"))
        living_room.child_objects.add_object(ItemObject("TV", "큰 대형TV, 한번도 켜진 적 없는 듯 먼지가 쌓여있다"))

        lim_room_list = [
            sleeping_room,
            living_room
        ]
        for room in lim_room_list:
            lim_house.child_objects.add_object(room)

        # 성당
        church = BuildingObject(
            name="성당",
            detail="성스러운 기운이 느껴지는 고요한 성당. 십자가와 제단이 중앙에 있다."
        )
        objects.append(church)

        prayer_room = SpaceObject("기도실", "제단이 있는 기도실. 성스러운 기운이 감도는 공간이다.")
        prayer_room.child_objects.add_object(ItemObject("예수님상", "제단에 서 있는 예수님상"))
        prayer_room.child_objects.add_object(ItemObject("의자", "성당앞에 서 있는 의자들"))
        
        garden = SpaceObject("조각상 정원", "성당 바깥쪽에 있는 조각상 정원. 성모마리아상이 가운데 서 있다.")
        garden.child_objects.add_object(ItemObject("성모마리아상", "정원 가운데 서 있는 성모마리아상"))

        church_room_list = [
            prayer_room,
            garden
        ]
        for room in church_room_list:
            church.child_objects.add_object(room)
        
        return objects