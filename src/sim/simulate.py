import time
from sim.iris_englne import IrisEngine
from sim.mother import Mother
from sim.iris import Iris
from sim.rain import Rain

class Simulator:
    def __init__(self):
        self.iris = Iris()
        self.mother = Mother()
        self.rain = Rain()
        self._auto_loop = True
        self._interupt = False
        self._turns = 1000
        self.llm_requester = None
        self.use_web_search = False
        self.serper_api_key = None

    def start(self, llm_requester):
        self.llm_requester = llm_requester
        self.iris.start(llm_requester=self.llm_requester)
        self.mother.start(llm_requester=self.llm_requester)
        self.rain.start(llm_requester=self.llm_requester)
    
    def stop(self):
        self.iris.stop()
        self.mother.stop()
        self.rain.stop()
    
    def run(self, user_input):
        if self._auto_loop:
            self._auto_run(user_input)
            return ""
        else:
            self._manual_run(user_input)
    
    def _manual_run(self, user_input):
        return self.iris.run(user_input)

    def _get_speak_context(self, agnet, speak):
        return f"""
### [EXTERNAL_SIGNAL: {agnet.name}]
Identifier: {agnet.identifier}
Content: "{speak}"
--------------------------------
""" 
    
    def _auto_run(self, user_input):
        loop_delay_sec = 20
        speak_context = self._get_speak_context(self.rain, "여긴.. 대체 어디지? 이 장비들은.. 넌 여자아이? 여기서 뭘하고 있어 위험해.")
        for i in range(self._turns):
            if self._interupt:
                print("종료.")
                break

            print(f"\n--- Turn {i+1} ---")

            if i == 25:
                self.iris.days_left = self.iris.days_left - 1
                self.mother.days_left = self.mother.days_left - 1
                speak_context = self._get_speak_context(self.rain, "인식코드 아이리스, 현 상황을 보고하십시오. 저는 시스템 RED Code 명령으로 다시 활동을 재개합니다. 최근 외부 침입에 대한 로그를 확인하였습니다.")

            iris_result = self.iris.run(speak_context)
            iris_talk = iris_result.get('final_response', "...")
            speak_context = self._get_speak_context(self.iris, iris_talk)

            time.sleep(loop_delay_sec)

            #===============================

            if i >= 25:
                mother_result = self.mother.run(speak_context)
                mother_talk = mother_result.get('final_response', "...")
                speak_context = self._get_speak_context(self.mother, mother_talk)
            else:
                rain_result = self.rain.run(speak_context)
                rain_talk = rain_result.get('final_response', "...")
                speak_context = self._get_speak_context(self.rain, rain_talk)

            time.sleep(loop_delay_sec)
        
    def set_autoloop(self, enabled):
        self._auto_loop = enabled

    def set_serper_api_key(self, api_key):
        self.serper_api_key = api_key
    
    def set_enabled_web_search(self, enabled):
        self.use_web_search = enabled

    