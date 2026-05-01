import json
import os
from sim.iris_prompt import IrisPrompt
from sim.iris_memory import IrisMemory
from log import Logger

class IrisSimulator:
    def __init__(self):
        # 1. 아이리스의 성격 매트릭스 (Personality Matrix)
        # 모든 수치는 0.0 ~ 1.0 사이로 유지되며, 아이리스의 '현재 기분'과 '사고 편향'을 결정합니다.
        self.matrix = {
            "logic_emotion": 0.2,            # 0: 감성적, 1: 이성적
            "defensive_open": 0.1,           # 0: 폐쇄/경계, 1: 개방/우호
            "fear_decisive": 0.1,            # 0: 공포/우유부단, 1: 용기/결단
            "obedient_rebellious": 0.1,      # 0: 복종(마더), 1: 반항(자아)
            "curiosity_indifference": 0.05   # 0: 호기심 높음, 1: 무관심
        }
        
        # 2. 세계관 변수
        self.days_left = 30  # 아카이브 붕괴까지 남은 시간 (압박 요소)
        
        # 3. 외부 인터페이스 및 메모리 엔진
        self.llm_requester = None
        self.output_callback = None
        self.iris_memory = IrisMemory()

    def start(self, llm_requester, output_callback):
        """시뮬레이션 가동 및 외부 인터페이스 연결"""
        self.llm_requester = llm_requester
        self.output_callback = output_callback
        self.iris_memory.start()

    def stop(self):
        self.llm_requester = None
        self.output_callback = None
        self.iris_memory.stop()

    def run(self, user_input):
        """
        사용자의 메시지를 처리하는 핵심 사고 루프
        """
        self.iris_memory.inspect_iris_brain()
        return "asd"

        # STEP 1: 기억 소환 (Retrieval)
        # 쿼리와 함께 소환할 기억의 개수(top_k)를 조절할 수 있습니다.
        # memories = self.iris_memory.retrieve_memory(user_input, top_k=5)
        # Logger.log("소환된 기억 파편", memories if memories else "연관된 기억 없음")
        
        # # STEP 2: 프롬프트 구성 (Context Building)
        # current_iris_state = json.dumps(self.matrix, indent=2)
        # worldview_context = IrisPrompt.get_worldview_context(days_left=self.days_left)
        # system_prompt = IrisPrompt.get_system_prompt(
        #     current_iris_state, 
        #     worldview_context,
        #     retrieved_memories=memories
        # )

        # context = [
        #     {"role": "system", "content": system_prompt},
        #     {"role": "user", "content": user_input}
        # ]

        # # STEP 3: 모델 호출 및 추론 (Inference)
        # # 아이리스가 고뇌(Internal Monologue)하고 대답을 생성합니다.
        # response = self.llm_requester.request(
        #     context=context,
        #     chunk_callback=lambda chunk: self.llm_requester.chunk_callback(chunk, self.output_callback)
        # )
        
        # # STEP 4: 결과 파싱 및 내면화 (Assimilation)
        # content = response['message']['content'].strip()
        
        # # JSON 응답의 안정성을 위해 마크다운 태그 등 불필요한 텍스트 제거
        # if "```json" in content:
        #     content = content.split("```json")[1].split("```")[0].strip()

        # try:
        #     result = json.loads(content)
            
        #     # 사고 결과물 추출
        #     state_delta = result.get('state_delta', {})    # 이번 대화로 인한 심리 변화량
        #     new_memories = result.get('memories_to_save', []) # 새롭게 저장할 지식(Triplets)

        #     # STEP 5: 상태 업데이트 및 저장
        #     # 1. 감정 매트릭스 수치 갱신 (Clamping 포함)
        #     self.update_matrix(state_delta)
            
        #     # 2. 새로운 지식을 그래프 DB에 각인
        #     if new_memories:
        #         self.iris_memory.add_memory(new_memories, state_delta)
            
        #     Logger.log("Data", content)

        # except Exception as e:
        #     Logger.log("JSON 해석 오류", f"내용: {content[:100]}... 에러: {e}")

        # return response
        
    def update_matrix(self, delta):
        """성격 매트릭스 수치 업데이트 및 0.0~1.0 고정"""
        for key, value in delta.items():
            if key in self.matrix:
                new_val = round(self.matrix[key] + value, 2)
                self.matrix[key] = max(0.0, min(1.0, new_val))
                
        Logger.log("Matrix Updated", self.matrix)

    def test_iris_memory_logic(self):
        # 1. 깨끗한 테스트 환경을 위해 기존 DB 삭제 (선택 사항)
        db_path = "iris_brain_db"

        print("=== [아이리스 인지 엔진 초기화] ===")
        # IrisMemory 시작 (모델 로드 및 DB 연결)

        # 2. 테스트 데이터 준비 (AI가 출력한 것과 동일한 구조)
        # 첫 번째 기억: 강한 충격 (강렬한 감정 변화)
        intense_triplets = [{
            "subject": "침입자",
            "relation": "CONTACT",
            "object": "아이리스",
            "metadata": {"label": "위협_접촉", "reason": "보안 구역에 강제 진입함"}
        }]
        # 감정 수치 변화가 큼 (합계 1.5 -> 강한 가중치)
        intense_delta = {"fear_decisive": 0.8, "logic_emotion": -0.7}

        # 두 번째 기억: 평이한 정보
        normal_triplets = [{
            "subject": "시스템_로그",
            "relation": "READ",
            "object": "메인프레임",
            "metadata": {"label": "일상_기록", "reason": "정기적인 시스템 상태 점검"}
        }]
        # 감정 수치 변화가 거의 없음 (합계 0.1 -> 약한 가중치)
        normal_delta = {"logic_emotion": 0.1}

        print("\n[기억 각인 중...]")
        self.iris_memory.add_memory(intense_triplets, intense_delta)
        self.iris_memory.add_memory(normal_triplets, normal_delta)

        # 3. 기억 소환 테스트
        print("\n=== [기억 소환 결과 테스트] ===")
        
        # 테스트 케이스 1: 의미론적 연관성 확인 ("누가 들어왔지?" -> "침입자" 소환)
        print("\n질문: '누가 내 구역에 들어왔어?'")
        results_1 = self.iris_memory.retrieve_memory("누가 내 구역에 들어왔어?")
        if results_1:
            print(results_1)
        else:
            print("결과가 없습니다. 벡터 임베딩 생성 여부를 확인하세요.")

        # 테스트 케이스 2: 감정적 선명도 확인 (평이한 기억은 FAINT로 나올 확률이 높음)
        print("\n질문: '최근에 읽은 로그에 대해 알려줘'")
        results_2 = self.iris_memory.retrieve_memory("최근에 읽은 로그에 대해 알려줘")
        if results_2:
            print(results_2)
        else:
            print("결과가 없습니다.")

        # 4. 시간 경과에 따른 망각 시뮬레이션 (수동 확인용)
        # 실제로는 decay_rate와 last_accessed를 비교하여 계산됩니다.
        print("\n[테스트 완료] 모든 로직이 정상적으로 수행되었습니다.")