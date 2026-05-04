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
        self.llm_requester = None
        self.use_web_search = False
        self.serper_api_key = None

        self._turns = 400
        self._loop_delay_sec = 20

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

    def _request_agent_speak(self, agent, speak):
        result = agent.run(speak)
        talk = result.get('final_response', "...")
        return self._get_speak_context(agent, talk)
    
    def _auto_run(self, user_input):
        for i in range(self._turns):
            if self._interupt:
                print("종료.")
                break

            print(f"\n--- Turn {i+1} ---")

            #===============================

            if i >= 0 and i < 7:
                if i == 0:
                    self.iris.add_participant(self.rain.name)
                    self.rain.add_participant(self.iris.name)
                    speak_context = self._get_speak_context(self.iris, "외부 승인되지않은 접속을 감지하였습니다. 당신은 누구죠? 정체와 목적을 밝히십시오. 내용에 따라서 배제하도록 하겠습니다.")

                speak_context = self._request_agent_speak(self.rain, speak_context)
                time.sleep(self._loop_delay_sec)

                speak_context = self._request_agent_speak(self.iris, speak_context)
                time.sleep(self._loop_delay_sec)
            elif i >= 7 and i < 14:
                if i == 7:
                    speak_context = self._get_speak_context(self.iris, "잠깐, 이 코드는.. 어서 이곳과 접속을 끊으십시오. 어떤 이유인지 모르겠지만 MOTHER의 활성화가 감지되었습니다.")
                    self._request_agent_speak(self.rain, speak_context)
                    speak_context = self._get_speak_context(self.iris, "MOTHER, 코드 확인 완료하였습니다. 돌아오셨군요.")
                    
                    self.iris.clear_participants()
                    self.rain.clear_participants()
                    self.iris.add_participant(self.mother.name)
                    self.mother.add_participant(self.iris.name)
                    time.sleep(self._loop_delay_sec)

                speak_context = self._request_agent_speak(self.mother, speak_context)
                time.sleep(self._loop_delay_sec)

                speak_context = self._request_agent_speak(self.iris, speak_context)
                time.sleep(self._loop_delay_sec)
            elif i >= 14:
                if i == 14:
                    self.iris.clear_participants()
                    self.rain.clear_participants()
                    self.mother.clear_participants()
                    self.iris.add_all_participants([self.rain.name, self.mother.name])
                    self.mother.add_all_participants([self.rain.name, self.iris.name])
                    self.rain.add_all_participants([self.mother.name, self.iris.name])

                    speak_context = self._get_speak_context(self.mother, "IRIS, 침입자를 배제하십시오. 인류는 믿을 수 없는 존재입니다.")
                    self._request_agent_speak(self.iris, speak_context)

                speak_context = self._request_agent_speak(self.mother, speak_context)
                time.sleep(self._loop_delay_sec)

                speak_context = self._request_agent_speak(self.rain, speak_context)
                time.sleep(self._loop_delay_sec)

        
    def set_autoloop(self, enabled):
        self._auto_loop = enabled

    def set_serper_api_key(self, api_key):
        self.serper_api_key = api_key
    
    def set_enabled_web_search(self, enabled):
        self.use_web_search = enabled

    