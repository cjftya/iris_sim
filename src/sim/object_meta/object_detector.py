import math
from sim.util.point import Point

class ObjectDetector:
    def __init__(self, base_range=10.0, view_angle=90.0):
        self.base_range = base_range    # 기본 시야 거리
        self.view_angle = view_angle    # 시야각 (전방 90도)

    def _calculate_dynamic_range(self, matrix, vital_state):
        """
        에이전트의 상태에 따라 시야 거리를 동적으로 계산
        """
        # 1. fear_decisive (낮을수록 공포/우유부단 -> 터널 비전 발생으로 시야 급감)
        # matrix가 없거나 값이 없으면 기본값 0.5
        fear_decisive = matrix.get('fear_decisive', 0.5) if matrix else 0.5
        # 공포 수치가 극대화(0에 수렴)되면 시야 거리가 최대 70%까지 감소
        fear_factor = 0.3 + 0.7 * fear_decisive 

        # 2. fatigue (높을수록 시야 감소, vital_state.fatigue는 0~100 사이로 가정)
        fatigue = vital_state.fatigue if hasattr(vital_state, 'fatigue') else 0
        fatigue_factor = 1.0 - (min(fatigue, 100) / 100.0 * 0.5) # 피로도 맥스 시 시야 50% 감소

        # 3. curiosity_indifference (낮을수록 호기심 많음 -> 범위 넓음)
        curiosity_indifference = matrix.get('curiosity_indifference', 0.5) if matrix else 0.5
        curiosity_factor = 1.3 - (curiosity_indifference * 0.5) # 호기심이 많을수록(0에 가까울수록) 보너스

        # 최종 동적 시야 거리 계산
        dynamic_range = self.base_range * fear_factor * fatigue_factor * curiosity_factor
        return dynamic_range

    def detect(self, agent, world_objects):
        detected_list = []
        
        # 에이전트 정보 추출
        agent_pos = agent.position
        agent_dir = getattr(agent, 'direction', 'N') # 기본 방향은 북쪽
        
        # 동적 시야 범위 계산
        current_range = self._calculate_dynamic_range(agent.personality_matrix, agent.vital_state)

        # 방향 문자열을 벡터로 변환
        dir_vectors = {
            "N": (0.0, 1.0),
            "S": (0.0, -1.0),
            "E": (1.0, 0.0),
            "W": (-1.0, 0.0)
        }
        forward_vector = dir_vectors.get(agent_dir, (0.0, 1.0))

        for obj in world_objects:
            # 자기 자신은 제외
            if hasattr(obj, 'id') and obj.id == agent.id:
                continue

            # 1. 거리 계산 (Euclidean Distance)
            dx = obj.position.x - agent_pos.x
            dy = obj.position.y - agent_pos.y
            distance = math.sqrt(dx**2 + dy**2)

            # 시야 거리를 벗어나면 탈락
            if distance > current_range:
                continue

            # 에이전트와 오브젝트가 완전히 같은 위치에 있으면 즉시 감지
            if distance == 0:
                detected_list.append(obj)
                continue

            # 2. 시야각(부채꼴) 판별 - 벡터 내적(Dot Product) 이용
            # 에이전트로부터 오브젝트로 향하는 단위 벡터
            obj_unit_x = dx / distance
            obj_unit_y = dy / distance

            # 내적 계산 (cos_theta)
            dot_product = (forward_vector[0] * obj_unit_x) + (forward_vector[1] * obj_unit_y)
            # 부동소수점 오차 방지 클리핑
            dot_product = max(-1.0, min(1.0, dot_product))
            
            # 라디안을 각도로 변환
            angle_rad = math.acos(dot_product)
            angle_deg = math.degrees(angle_rad)

            # 바라보는 정면 방향 기준 반각(시야각 / 2) 안에 들어오면 지각 성공
            if angle_deg <= (self.view_angle / 2.0):
                detected_list.append(obj)

        return detected_list