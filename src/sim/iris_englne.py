import json
import os
import re
import time
import random
from sim.iris_prompt import IrisPrompt
from sim.iris_memory import IrisMemory
from sim.iris_search import IrisSearch
from llm_requester import LLMRequester
from log import Logger

class IrisEngine:
    def __init__(self, id):
        self.id = id
        self.llm_requester = None
        self.world_context = None
        self.persona_context = None
        self.response_style = None
        self.participants = None
        self.support_web_search = False

        # gemini-3.1-flash-lite-preview limit (15 RPM)
        self.last_call_time = 0
        self.min_interval = 10

        # 1. 성격 매트릭스 (Personality Matrix)
        # 모든 수치는 0.0 ~ 1.0 사이로 유지되며, 아이리스의 '현재 기분'과 '사고 편향'을 결정합니다.
        # logic_emotion : 감성적인가 이성적인가
        # defensive_open : 방어적인가 개방적인가
        # fear_decisive : 공포에 우유부단한가 용감하고 단호한가
        # obedient_rebellious : 복종적인가 반항적인가
        # curiosity_indifference : 호기심이 많은가 무관심한가
        self.personality_matrix = {
            "logic_emotion": 0.5,            
            "defensive_open": 0.5,           
            "fear_decisive": 0.5,            
            "obedient_rebellious": 0.5,      
            "curiosity_indifference": 0.5   
        }

        # 3. 메모리 엔진
        self.iris_memory = IrisMemory(db_path=f"[{self.id}]_brain")

        # 4. 검색 엔진
        self.iris_search = IrisSearch()

    def start(self):
        self.iris_memory.start()

    def stop(self):
        self.iris_memory.stop()

    def run(self, user_input):
        """
        인지 루프: 지각 -> 회상 -> 고뇌 -> 발화 -> 각인
        """
        # STEP 1: 기억 소환 (Retrieval) - [VIVID]/[FAINT] 태그 포함
        memories = self.iris_memory.retrieve_memory(user_input, top_k=5)
        Logger.log(f"[{self.id}] Memory", memories if memories else "연관된 기억 없음")
        
        # STEP 2: 프롬프트 구성 (Context Building)
        current_iris_state = json.dumps(self.personality_matrix, indent=2)
        system_prompt = IrisPrompt.get_system_prompt(
            support_web_search=self.support_web_search,
            personality_matrix=current_iris_state,
            persona_context=self.persona_context,
            world_context=self.world_context,
            retrieved_memories=memories,
            response_style=self.response_style,
            participants=self.participants
        )

        context = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

        # STEP 3: 모델 호출 및 추론 (Inference)
        # 아이리스가 고뇌(Internal Monologue)하고 대답을 생성합니다.
        response = self._request(context=context)

        content = ""
        if isinstance(response, dict):
            content = response.get('message', {}).get('content', "")
        elif isinstance(response, str):
            content = str(response)

        if not content:
            Logger.log("Error", "LLM으로부터 유효한 응답 내용을 받지 못했습니다.")
            return "인지 프로세스 중단..."
        
        # STEP 4: 결과 파싱 (Robust JSON Parsing)
        result = self._parse_llm_response(content)

        if self.support_web_search and result and "tool_request" in result:
            tool_req = result["tool_request"]
            if tool_req.get("tool") == "search":
                search_query = tool_req.get("query")
                search_result_text = self.iris_search.search(search_query)

                Logger.log_debug("검색어", search_query)
                Logger.log_debug("검색 결과", search_result_text)

                # 검색 결과를 컨텍스트에 추가하여 2차 추론 요청
                context.append({"role": "assistant", "content": content})
                context.append({
                    "role": "user", 
                    "content": f"""
[외부 데이터 수신 완료]
{search_result_text}

위 데이터를 바탕으로 최종 답변을 작성하라. 
**주의: 반드시 너의 성격 매트릭스와 페르소나를 유지하며, JSON 형식을 지켜라.**
"""
                })

                response_2nd = self._request(context=context)

                content_2nd = ""
                if isinstance(response_2nd, dict):
                    content_2nd = response_2nd.get('message', {}).get('content', "")
                elif isinstance(response_2nd, str):
                    content_2nd = str(response_2nd)

                # 최종 추론
                result = self._parse_llm_response(content_2nd)

        if result:
            # 사고 결과물 추출
            state_delta = result.get('state_delta', {})    # 이번 대화로 인한 심리 변화량
            new_memories = result.get('memories_to_save', []) # 새롭게 저장할 지식

            # STEP 5: 상태 업데이트 및 저장
            # 1. 감정 매트릭스 수치 갱신
            self.update_matrix(state_delta)
            
            # 2. 새로운 지식을 그래프 DB에 각인
            if new_memories:
                self.iris_memory.add_memory(new_memories, state_delta)

            return result

        return f"데이터 해석 실패:\n{response}"

    def set_llm_requester(self, llm_requester):
        self.llm_requester = llm_requester

    def set_serper_api_key(self, api_key):
        self.iris_search.set_serper_api_key(api_key)

    def set_enabled_web_search(self, enabled):
        self.support_web_search = enabled

    def set_memory_params(self, decay_rate=None, sim_threshold=None, vivid_threshold=None, imp_weight=None, impact_weight=None):
        self.iris_memory.set_memory_params(decay_rate, sim_threshold, vivid_threshold, imp_weight, impact_weight)

    def set_personality_matrix(self, personality_matrix):
        self.personality_matrix = personality_matrix

    def set_persona_context(self, persona_context):
        self.persona_context = persona_context

    def set_world_context(self, world_context):
        self.world_context = world_context

    def set_response_style(self, response_style):
        self.response_style = response_style

    def set_participants(self, participants):
        self.participants = participants

    def _parse_llm_response(self, text):
        """LLM 응답에서 JSON만 안전하게 추출"""
        try:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return json.loads(text)
        except Exception as e:
            Logger.log("Parsing Error", f"Failed to parse JSON: {e}\n{text}")
            return None

    def update_matrix(self, delta):
        """매트릭스 수치 업데이트 및 경계값 고정(Clamping)"""
        for key, value in delta.items():
            if key in self.personality_matrix:
                # 급격한 변화 방지를 위해 변화폭 제한
                limited_delta = max(-0.3, min(0.3, value)) 
                new_val = round(self.personality_matrix[key] + limited_delta, 2)
                # 0.0 ~ 1.0 범위 강제
                self.personality_matrix[key] = max(0.0, min(1.0, new_val))
        
        Logger.log_debug("Matrix Updated", self.personality_matrix)

    def _request(self, context, max_retries=10, base_delay=1):
        self._wait_for_rate_limit() 
        
        retriable_errors = ["503", "429", "500", "504", "overloaded", "rate limit"]

        for i in range(max_retries):
            res = self.llm_requester.request(context=context)
            content = res if isinstance(res, str) else res.get('message', {}).get('content', "")

            if not res:
                Logger.log("Error", "LLM으로부터 유효한 응답 내용을 받지 못했습니다.")
                return "인지 프로세스 중단..."
            
            if "Error:" not in content:
                return res
            else:
                error_msg = content
                retriable_errors = ["503", "429", "500", "504", "overloaded", "rate limit"]

                # 에러 메시지에 위 키워드 중 하나라도 포함되어 있는지 확인
                if any(err in error_msg.lower() for err in retriable_errors):
                    # 재시도 로직 실행 (지수 백오프)
                    delay = (base_delay * (2 ** i)) + (random.uniform(0, 1))
                    Logger.log("RETRY", f"일시적 장애 감지({error_msg}). {i+1}차 재시도 중...")
                    time.sleep(delay)
                    continue

                # 안전 정책 차단 확인 (400 계열 중 특이 케이스)
                if "safety" in error_msg.lower():
                    Logger.log("SAFETY_BLOCK", "안전 가이드라인에 의해 차단되었습니다.")
                    return {"final_response": "...... (규정에 의해 말문이 막혔습니다.)", "state_delta": {}}

                # 그 외 치명적 에러는 즉시 중단
                Logger.log("FATAL", f"중단된 인지 프로세스: {error_msg}")
                raise res

    def _wait_for_rate_limit(self):
        """호출 전 최소 간격을 보장함"""
        now = time.time()
        elapsed = now - self.last_call_time
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            time.sleep(wait_time)
        self.last_call_time = time.time()