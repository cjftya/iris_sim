from log import Logger

class IrisFunction:
    def __init__(self):
        self.action_map = {
            "move_to": self._move_to,
            "speak": self._speak,
            "take": self._take,
            "give": self._give,
            "attack": self._attack,
            "search": self._search,
            "use": self._use,
            "rest": self._rest,
            "none": self._none_action
        }

    def process_action_call(self, action_call, agent):
        function_name = action_call.get('function')
        if function_name not in self.action_map:
            Logger.log_debug(f"skip function call: {function_name}")
            return
        
        parameters = action_call.get('parameters', {})
        try:
            self.action_map[function_name](parameters, agent)
        except Exception as e:
            Logger.log_debug(f"Action Execution Error ({function_name})", e)

    # 1. 이동: move_to(location)
    def _move_to(self, params, agent):
        location = params.get('location', None)
        reason = params.get('reason', None)
        if location and location in agent.available_locations:
            agent.current_location = location
            agent.reason_of_change_location = reason
        else:
            Logger.log_debug(f"skip function call: move_to, location: {location}")

    # 2. 사회: speak(target, message)
    def _speak(self, params, agent):
        target = params.get('target', 'ALL')
        message = params.get('message', '')
        Logger.log_debug("Social", f"[{target}]에게 메시지 송신: {message}")

    # 3. 소유: take(item)
    def _take(self, params, agent):
        item_id = params.get('item')
        Logger.log_debug("Inventory", f"{item_id} 획득 시도")

    # 4. 사회: give(target, item)
    def _give(self, params, agent):
        target = params.get('target')
        item_id = params.get('item')
        Logger.log_debug("Social", f"{target}에게 {item_id} 전달")

    # 5. 전투: attack(target, intensity)
    def _attack(self, params, agent):
        target = params.get('target')
        intensity = params.get('intensity', 0.5)
        Logger.log_debug("Combat", f"{target} 공격 (강도: {intensity})")

    # 6. 지각: search(area)
    def _search(self, params, agent):
        area = params.get('area', 'current_location')
        Logger.log_debug("Perception", f"{area} 정밀 탐색 수행")

    # 7. 상호작용: use(target, item)
    def _use(self, params, agent):
        target = params.get('target') # 오브젝트 혹은 자기 자신
        item = params.get('item')     # 사용할 아이템
        Logger.log_debug("Interaction", f"{item}을(를) 사용하여 {target} 조작")

    # 8. 생존: rest()
    def _rest(self, params, agent):
        Logger.log_debug("Survival", "휴식 및 인지 정리 루틴 시작")
        if hasattr(agent.iris_engine, 'iris_memory'):
            agent.iris_engine.iris_memory.perform_brain_cleanup()

    # 9. 정지: none()
    def _none_action(self, params, agent):
        pass