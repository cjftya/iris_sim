import random

class EventType:
    NO_EVENT = 0
    HUNGER_TRIPPED = 1
    FATIGUE_TRIPPED = 2
    RANDOM_SCAN = 3
    PROACTIVE_PULSE = 4
    CRITICAL_PULSE = 5

class ThinkEventType:
    NO_EVENT = 0
    FIND_ITEM = 1
    FIND_AGENT = 2
    SPEAK = 3
    HUNGER = 4
    FATIGUE = 5
    INSPECT = 6
    PLANNING = 7


class EventTrigger:
    def __init__(self):
        self.move_timer = 0
        self.scan_timer = 0
        self.plan_timer = 0

    def stop(self):
        self.move_timer = -99999
        self.scan_timer = -99999
        self.plan_timer = -99999
    
    def check_triggers(self, agents, time_scale=1.0):
        self.move_timer += time_scale
        self.scan_timer += time_scale
        self.plan_timer += time_scale

        event_pack = []
        
        # 신체적 결핍 신호
        for agent in agents:
            vital = agent.get_vital_state()
            if vital.hunger >= 80.0:
                event_pack.append([agent, EventType.HUNGER_TRIPPED, "[EXTERNAL_SIGNAL: 생체 위기] 배고픔이 한계에 달해 속이 쓰리고 고통스럽다."])

            if vital.fatigue >= 80.0:
                event_pack.append([agent, EventType.FATIGUE_TRIPPED, "[EXTERNAL_SIGNAL: 생체 위기] 극심한 피로로 인해 눈꺼풀이 무겁고 정신이 흐려진다."])

        if len(event_pack) > 0:
            self.plan_timer = 0
            self.scan_timer = 0
            self.move_timer = 0
            return event_pack

        PLAN_INTERVAL = 20 / 60.0  # 인게임 기준 '20분' 마다 확실한 기획 제공
        MOVE_INTERVAL = 12 / 60.0  # 인게임 기준 최소 '12분' 정체 시 충동 검사
        SCAN_INTERVAL = 15 / 60.0  # 인게임 기준 '15분' 마다 스캔 검사

        # 독립된 계획 신호
        if self.plan_timer >= PLAN_INTERVAL:
            self.plan_timer = 0
            for agent in agents:
                event_pack.append([agent, EventType.PROACTIVE_PULSE, "[EXTERNAL_SIGNAL: 자율 계획] 현재 상황을 종합적으로 분석하고, 당신의 궁극적인 목표를 달성하기 위한 단계별 행동 전략을 수립하라."])
            return event_pack

        # 고립 탈출 신호
        if self.move_timer >= MOVE_INTERVAL and random.random() < 0.10:
            self.move_timer = 0
            for agent in agents:
                event_pack.append([agent, EventType.CRITICAL_PULSE, "[EXTERNAL_SIGNAL: 위기 탈출] 현재 상황이나 행동 루틴에서 더 이상 새로운 진전이 없는 것 같다. 고착된 상태를 깨고, 다음 단계나 새로운 돌파구를 모색해야겠다는 생각이 든다."])
            return event_pack

        # 스캔 신호
        if self.scan_timer >= SCAN_INTERVAL and random.random() < 0.05:
            self.scan_timer = 0
            event_pack.append([None, EventType.RANDOM_SCAN, "[EXTERNAL_SIGNAL: 환경 스캔] 주변 환경을 확인하라."])
            return event_pack

        event_pack.append([None, EventType.NO_EVENT, "..."])
        return event_pack


                