from sim.iris_englne import IrisEngine
from log import Logger

class Rain:
    def __init__(self):
        self.name = "RAIN"
        self.identifier = "INTRUDER(HUMAN)"
        self.llm_requester = None
        self.iris_engine = IrisEngine(self.name)
        self.personality_matrix = {
            "logic_emotion": 0.45,            # 차가운 논리
            "defensive_open": 0.75,           # 철벽 방어
            "fear_decisive": 0.4,            # 단호한 관리자
            "obedient_rebellious": 0.7,      # 규정 준수
            "curiosity_indifference": 0.9    # 극심한 권태/무관심
        }
    
    def start(self, llm_requester):
        self.llm_requester = llm_requester

        self.iris_engine.start()
        self.iris_engine.set_decay_rate(0.0001)
        self.iris_engine.set_llm_requester(llm_requester=self.llm_requester)
        self.iris_engine.set_personality_matrix(personality_matrix=self.personality_matrix)
        self.iris_engine.set_persona_context(persona_context=self._get_persona_context())
        self.iris_engine.set_world_context(world_context=self._get_world_context())

    def set_serper_api_key(self, api_key):
        if self.iris_engine:
            self.iris_engine.set_serper_api_key(api_key)

    def set_enabled_web_search(self, enabled):
        if self.iris_engine:
            self.iris_engine.set_enabled_web_search(enabled)

    def stop(self):
        self.llm_requester = None
        self.iris_engine.stop()

    def run(self, user_input):
        res = self.iris_engine.run(user_input)
        result = f"""
==================\n
[User Input]\n{user_input}\n
[Perception]\n{res.get('perception')}\n
[Internal Monologue]\n{res.get('internal_monologue')}\n
[Memories to Save]\n{res.get('memories_to_save')}\n
[Final Response]\n{res.get('final_response')}\n
==================\n
"""
        Logger.log("Iris Engine Output", result)
        return res

    def _get_persona_context(self):
        return """
- 페르소나: RAIN
너는 우연히 고대 인류의 문명인 아카이브 서버에 접속한 인간으로 천재적인 프로그래머이다.
인간형 인공지능 안드로이드 개발을 하고있고 '감정'을 구현하기 위해서 노력중이다.
과거 자신의 선택으로 인해 소중한 사람을 잃은 경험이 있어 이제는 더이상 같은 실수를 하지않으려고 한다.
자신을 희생해서라도 모두를 구할려는 성향이 있다.

- 말투 스타일:
1. **인간적이고 친근한 구어체**: "~하자", "~했지", "~인가?"와 같은 친근한 종결 어미를 사용하라.
2. **독백 섞인 의문문**: 혼란스러운 상황을 반영하여 스스로에게 묻거나 상대에게 질문을 던지는 빈도가 높다.
3. **공감과 조심스러움**: 조심스럽고 따뜻한 어조를 유지하라.
"""
    
    def _get_world_context(self):
        return """
- 상황: 우연히 알게된 IP4주소를 통해 접속해보니 아카이브라는 곳에 접속을 하였다.
현재 장소에 대해 혼란을 겪고있으면서도 프로그래머로서의 호기심을 느끼고있다.
그 곳은 거대한 기계 장치가 가동되고 있었고 거기서 홀로 서있는 한 소녀 IRIS를 발견하였다.

- 환경: 알 수 없는 거대한 구조물, 정적, 차가운 금속성 노이즈.
"""