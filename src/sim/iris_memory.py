import kuzu
import time
import numpy as np
from sentence_transformers import SentenceTransformer

class IrisMemory:
    def __init__(self, db_path="iris_brain_db"):
        # 그래프 데이터베이스 및 연결 초기화
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        
        # 의미론적 검색을 위한 로컬 임베딩 모델 로드 (BGE-M3)
        self.embed_model = SentenceTransformer("./models/bge-m3") 

        # --- 커스텀 가능 인지 매개변수 ---
        self.decay_rate = 0.0001          # 망각 속도: 값이 커질수록 시간이 지남에 따라 기억이 빨리 흐려짐
        self.sim_threshold = 0.3          # 유사도 임계값: 검색 쿼리와 관련성이 낮은 노이즈 기억을 필터링
        self.vivid_threshold = 0.8        # 선명도 기준: 최종 점수가 이 값을 넘으면 [VIVID], 낮으면 [FAINT]로 판정
        self.imp_weight = 0.7             # 기억 각인 시 '주관적 중요도'의 반영 비중
        self.impact_weight = 0.3          # 기억 각인 시 '시스템적 충격량'의 반영 비중

    def set_memory_params(self, decay_rate=None, sim_threshold=None, vivid_threshold=None, imp_weight=None, impact_weight=None):
        """
        외부(시뮬레이션 환경)에서 엔진의 인지 특성을 실시간으로 조정합니다.
        예: 스트레스 상황에서 망각 속도를 높이거나 각인 강도를 조정할 때 사용합니다.
        """
        if decay_rate is not None: self.decay_rate = decay_rate
        if sim_threshold is not None: self.sim_threshold = sim_threshold
        if vivid_threshold is not None: self.vivid_threshold = vivid_threshold
        if imp_weight is not None: self.imp_weight = imp_weight
        if impact_weight is not None: self.impact_weight = impact_weight

    def start(self):
        """DB 스키마를 준비하고 엔진을 가동합니다."""
        self._prepare_schema()

    def stop(self):
        """DB 연결을 안전하게 종료합니다."""
        if self.conn:
            self.conn.close()
        self.db.close()

    def _prepare_schema(self):
        """
        지식 그래프를 위한 노드(node) 및 관계(rel) 테이블 스키마를 생성합니다.
        관계 테이블에는 인지적 특성(강도, 빈도, 중요도, 감정 가치 등)이 저장됩니다.
        """
        # intensity: 각 노드(단어/개념) 자체의 '존재감' 또는 '고유한 강도'
        # last_accessed: 마지막으로 기억을 인출한 시간. 이 시간이 오래될수록 '망각'이 진행됨
        # frequency: 얼마나 자주 인출되었는가. 빈도가 높을수록 뇌 속에 깊이 각인됨
        # sub_label: LLM이 부여한 주관적인 관계 이름표. (예: 친구, 적, 어머니)
        # interpretation: 해당 기억이 왜 중요한지, 또는 어떻게 해석되는지에 대한 설명. (예: "중요한 결정의 원인이 되었음")
        # importance: 자아 형성에 미치는 영향력. 높을수록 에이전트의 정체성에 큰 영향을 미침
        # valence: 기억의 감정적 색채. 긍정(1)에서 부정(-1)까지의 값으로, 강렬한 감정은 더 오래 기억됨
        
        try:
            self.conn.execute("CREATE NODE TABLE node (id STRING, embedding DOUBLE[], PRIMARY KEY (id))")
            self.conn.execute("""
                CREATE REL TABLE rel (
                    FROM node TO node, 
                    intensity DOUBLE,
                    last_accessed DOUBLE,
                    frequency INT64,
                    sub_label STRING,
                    interpretation STRING,
                    importance DOUBLE,
                    valence DOUBLE,
                    MANY_MANY
                )
            """)
        except Exception:
            # 이미 스키마가 존재할 경우 무시합니다.
            pass

    def add_memory(self, triplets, state_delta):
        """
        새로운 대화 파편을 뇌(DB)에 새깁니다.
        state_delta를 통해 현재의 심리적 충격을 계산하고, 중요도와 결합하여 각인 강도를 결정합니다.
        """
        # 현재 대화로 인한 시스템 수치 변화량의 합산 (충격량 계산)
        state_impact = sum(abs(v) for v in state_delta.values() if isinstance(v, (int, float)))
        now = time.time()

        for t in triplets:
            subj, rel, obj = t['subject'], t['relation'], t['object']
            meta = t.get('metadata', {})

            # LLM이 판단한 주관적 지표 추출
            importance = float(meta.get('importance', 0.5))
            valence = float(meta.get('valence', 0.0))

            # 최종 각인 강도 결정: 주관적 중요도와 객관적 충격을 멤버 가중치에 따라 합산
            memory_intensity = (importance * self.imp_weight) + (state_impact * self.impact_weight)
            
            # 텍스트 데이터를 벡터로 변환하여 노드 임베딩 생성
            subj_emb = self.embed_model.encode(subj).tolist()
            obj_emb = self.embed_model.encode(obj).tolist()
            
            # 1. 노드 생성 또는 업데이트 (MERGE)
            self.conn.execute(
                "MERGE (n:node {id: $id}) SET n.embedding = $emb", 
                {"id": subj, "emb": subj_emb}
            )
            self.conn.execute(
                "MERGE (n:node {id: $id}) SET n.embedding = $emb", 
                {"id": obj, "emb": obj_emb}
            )

            # 2. 관계(뉴럴 링크) 생성 또는 빈도 누적 업데이트
            # ON MATCH 시 강도를 점진적으로 업데이트하여 '학습' 효과 구현
            self.conn.execute(f"""
                MATCH (s:node {{id: $subj}}), (o:node {{id: $obj}})
                MERGE (s)-[r:rel]->(o)
                ON CREATE SET 
                    r.intensity = $intensity,
                    r.frequency = 1,
                    r.last_accessed = $now,
                    r.sub_label = $label,
                    r.interpretation = $reason,
                    r.importance = $importance,
                    r.valence = $valence
                ON MATCH SET 
                    r.intensity = (r.intensity * 0.4) + ($intensity * 0.6),
                    r.frequency = r.frequency + 1,
                    r.last_accessed = $now,
                    r.importance = $importance,
                    r.valence = $valence
            """, {
                    "subj": subj, "obj": obj, "intensity": memory_intensity, 
                    "now": now, "label": meta.get('label', rel), 
                    "reason": str(meta.get('reason', '')),
                    "importance": importance, "valence": valence
            })

    def retrieve_memory(self, query, top_k=5):
        """
        주어진 질문(Query)과 관련된 기억을 인간의 회상 원리에 따라 인출합니다.
        유사도, 망각, 중요도, 감정이 복합적으로 작용합니다.
        """
        query_emb = self.embed_model.encode(query).tolist()
        now = time.time()
        
        # 모든 인지망 관계 탐색
        res = self.conn.execute("""
            MATCH (n:node)-[r:rel]->(o:node)
            RETURN n.id, o.id, r.intensity, r.frequency, r.last_accessed, r.sub_label, n.embedding, r.importance, r.valence
        """)

        candidates = []
        while res.has_next():
            row = res.get_next()
            subj, obj, intensity, freq, last_time, sub_label, node_emb, imp, val = row
            
            # 1. 의미 유사도 계산 (코사인 유사도)
            sim = np.dot(query_emb, node_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(node_emb))
            
            # 노이즈 필터링: 유사도가 너무 낮으면 기억해내지 못함
            if sim < self.sim_threshold: continue

            # 2. 망각 곡선 적용: 시간이 흐를수록 약화되나, 중요도(imp)가 높을수록 저항함
            # 수식: 강도 = (기초강도 * 빈도 * 중요도보정) / (1 + 망각속도 * 경과시간)
            time_diff = now - last_time
            memory_strength = (intensity * freq * (1 + imp)) / (1 + self.decay_rate * time_diff)

            # 3. 감정적 편향: Valence의 절대값이 클수록(강렬한 감정일수록) 더 선명하게 회상됨
            emotional_weight = 1 + abs(val)
            
            # 최종 회상 점수 계산
            final_score = sim * memory_strength * emotional_weight
            
            candidates.append({
                "score": final_score,
                "text": f"{subj} --({sub_label})--> {obj}",
                "importance": imp,
                "valence": val,
                # 임계값에 따라 선명도 태그 부여 (프롬프트 엔진에서 활용)
                "intensity": "VIVID" if final_score > self.vivid_threshold else "FAINT" 
            })

        # 점수가 높은 순(가장 선명한 기억)으로 정렬하여 반환
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return "\n".join([
            f"- [{c['intensity']}] {c['text']} (Valence: {c['valence']:.1f}, Score: {c['score']:.2f})" 
            for c in candidates[:top_k]
        ])

    def inspect_iris_brain(self):
        """
        현재 에이전트의 뇌 구조를 시각화하여 터미널에 출력합니다.
        각 기억의 중요도와 감정 상태, 해석을 한눈에 확인할 수 있습니다.
        """
        try:
            print(f"\n" + "═"*80)
            print(f"🧠 [Project Iris] 범용적 뇌(Universal Brain) 뉴럴 링크 진단")
            print("═"*80)

            rels_res = self.conn.execute("""
                MATCH (s:node)-[r:rel]->(o:node) 
                RETURN s.id, r.sub_label, r.importance, r.valence, r.frequency, r.last_accessed, o.id, r.interpretation
            """)
            
            print(f"{'관계(Relation)':<35} | {'중요도':<4} | {'가치':<4} | {'심리적 이름표'}")
            print("─"*80)

            while rels_res.has_next():
                s, label, imp, val, freq, last, o, reason = rels_res.get_next()
                relation_str = f"{s} → {label} → {o}"
                # 관계의 주관적 가치(Valence)와 중요도(Importance)를 정렬하여 출력
                print(f"{relation_str:<35} | {imp:<6.1f} | {val:<6.1f} | {reason}")

            print("═"*80)
        except Exception as e:
            print(f"❌ DB 조회 실패: {e}")