import kuzu
import time
import numpy as np
from sentence_transformers import SentenceTransformer
from log import Logger

class IrisMemory:
    def __init__(self, db_path="iris_brain_db", load_embed_model=True):
        # 그래프 데이터베이스 및 연결 초기화
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        
        # 의미론적 검색을 위한 로컬 임베딩 모델 로드 (BGE-M3)
        if load_embed_model:
            self.embed_model = SentenceTransformer("./models/bge-m3") 
        else:
            self.embed_model = None

        # --- 커스텀 가능 인지 매개변수 (최적화됨) ---
        self.decay_rate = 0.0001          # 망각 속도
        self.sim_threshold = 0.45         # 유사도 임계값 상향 (노이즈 필터링 강화)
        self.vivid_threshold = 0.85       # 선명도 기준 상향
        self.imp_weight = 0.7             # 주관적 중요도 비중
        self.impact_weight = 0.3          # 시스템적 충격량 비중

    def start(self):
        self._prepare_schema()

    def stop(self):
        if self.conn:
            self.conn.close()
        self.db.close()

    def _prepare_schema(self):
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
            pass

    def add_memory(self, triplets, state_delta):
        """새로운 대화 파편을 뇌(DB)에 새깁니다."""
        # 충격량 계산 (절대값 합산)
        state_impact = sum(abs(v) for v in state_delta.values() if isinstance(v, (int, float)))
        now = time.time()

        for t in triplets:
            subj, rel, obj = t['subject'], t['relation'], t['object']
            meta = t.get('metadata', {})

            importance = float(meta.get('importance', 0.5))
            valence = float(meta.get('valence', 0.0))

            # 각인 강도 결정
            memory_intensity = (importance * self.imp_weight) + (state_impact * self.impact_weight)
            
            subj_emb = self.embed_model.encode(subj).tolist()
            obj_emb = self.embed_model.encode(obj).tolist()
            
            # 1. 노드 생성 또는 업데이트
            self.conn.execute(
                "MERGE (n:node {id: $id}) SET n.embedding = $emb", 
                {"id": subj, "emb": subj_emb}
            )
            self.conn.execute(
                "MERGE (n:node {id: $id}) SET n.embedding = $emb", 
                {"id": obj, "emb": obj_emb}
            )

            # 2. 관계 생성 또는 업데이트 (기존 로직 유지)
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

    def retrieve_memory(self, query, current_valence=0.0, top_k=3):
        """
        현재 감정 상태(current_valence)를 반영하여 기억을 인출합니다.
        가중치: 유사도(Semantic) + 망각 저항(Importance) + 감정 일치(Mood Congruence)
        """
        query_emb = self.embed_model.encode(query).tolist()
        now = time.time()
        
        res = self.conn.execute("""
            MATCH (n:node)-[r:rel]->(o:node)
            RETURN n.id, o.id, r.intensity, r.frequency, r.last_accessed, r.sub_label, n.embedding, r.importance, r.valence
        """)

        candidates = []
        while res.has_next():
            row = res.get_next()
            subj, obj, intensity, freq, last_time, sub_label, node_emb, imp, val = row
            
            # 1. 의미 유사도 (코사인 유사도)
            sim = np.dot(query_emb, node_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(node_emb))
            if sim < self.sim_threshold: continue

            # 2. 가변 망각 곡선 (Importance-driven Decay)
            # 중요도(imp)가 높을수록 망각 속도가 기하급수적으로 느려짐
            time_diff = now - last_time
            effective_decay = self.decay_rate / (1 + (imp * 15)) # 중요 기억은 거의 망각되지 않음
            memory_strength = (intensity * freq * (1 + imp)) / (1 + effective_decay * time_diff)

            # 3. 감정 일치 가중치 (Mood Congruence Weight)
            # 현재 기분(current_valence)과 기억의 가치(val)가 같은 방향일 때 더 잘 떠오름
            # 예: 기분이 나쁠 때(-0.5) 나쁜 기억(-0.8)을 보면 mood_match는 0.4(양수)가 되어 가중됨
            mood_match = current_valence * val
            # 감정적 강도(절대값)와 일치도(mood_match)를 결합
            emotional_weight = 1 + abs(val) + (max(0, mood_match) * 0.8)
            
            # 최종 회상 점수
            final_score = sim * memory_strength * emotional_weight
            
            candidates.append({
                "score": final_score,
                "text": f"{subj} --({sub_label})--> {obj}",
                "importance": imp,
                "valence": val,
                "intensity": "VIVID" if final_score > self.vivid_threshold else "FAINT" 
            })

        # 점수 순 정렬 및 상위 k개 반환
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        result_texts = []
        for c in candidates[:top_k]:
            tag = f"[{c['intensity']}]"
            valence_str = "POS" if c['valence'] > 0.1 else "NEG" if c['valence'] < -0.1 else "NEU"
            result_texts.append(f"- {tag} {c['text']} ({valence_str}, Imp: {c['importance']:.1f})")

        return "\n".join(result_texts)

    def perform_brain_cleanup(self, strength_threshold=0.1):
        """
        [GC] 흐릿해진 기억을 삭제하고 뇌 구조를 최적화합니다.
        """
        now = time.time()
        
        # 1. 약해진 관계(시냅스) 삭제
        # 수식: (intensity * freq * (1 + imp)) / (1 + decay * time_diff) < threshold
        self.conn.execute(f"""
            MATCH ()-[r:rel]->()
            WHERE (r.intensity * r.frequency * (1 + r.importance)) / 
                (1 + {self.decay_rate} * ({now} - r.last_accessed)) < {strength_threshold}
            DELETE r
        """)
        
        # 2. 연결된 관계가 없는 고립 노드 삭제
        self.conn.execute("""
            MATCH (n:node)
            WHERE NOT (n)-[:rel]-()
            DELETE n
        """)
        
        Logger.log_debug("[GC] 잠을 자며 불필요한 시냅스를 정리했습니다.")

    def get_visual_data(self):
        """DB 구조 변경 없이 시각화 데이터만 추출"""
        try:
            # 스키마에 존재하는 n.id만 쿼리합니다.
            nodes_res = self.conn.execute("MATCH (n:node) RETURN n.id") 
            nodes = []
            while nodes_res.has_next(): 
                row = nodes_res.get_next()
                node_id = str(row[0])
                nodes.append({
                    "id": node_id, 
                    "desc": f"Neural node: {node_id}"
                })

            # 관계 데이터 추출 (기존 필드 유지)
            links_res = self.conn.execute("""
                MATCH (s:node)-[r:rel]->(o:node) 
                RETURN s.id, o.id, r.intensity, r.sub_label, r.importance, r.valence
            """)
            links = []
            while links_res.has_next():
                row = links_res.get_next()
                links.append({
                    "source": str(row[0]),
                    "target": str(row[1]),
                    "intensity": float(row[2]) if row[2] else 1.0,
                    "label": str(row[3]) if row[3] else "",
                    "importance": float(row[4]) if row[4] else 0.5,
                    "valence": float(row[5]) if row[5] else 0.0
                })

            return {"nodes": nodes, "links": links}
        except Exception as e:
            print(f"❌ [Visual Data Error]: {e}")
            return {"nodes": [], "links": []}

    def set_memory_params(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def inspect_iris_brain(self):
        """기존 진단 로직 유지"""
        try:
            Logger.log(f"\n" + "═"*80)
            Logger.log(f"🧠 [Project Iris] 인지망(Neural Links) 정밀 진단")
            Logger.log("═"*80)

            rels_res = self.conn.execute("""
                MATCH (s:node)-[r:rel]->(o:node) 
                RETURN s.id, r.sub_label, r.importance, r.valence, r.frequency, r.intensity, o.id, r.interpretation
            """)
            
            Logger.log(f"{'뉴럴 링크(Relation)':<40} | {'중요도':<4} | {'감정가':<4} | {'해석/맥락'}")
            Logger.log("─"*80)

            while rels_res.has_next():
                s, label, imp, val, freq, inten, o, reason = rels_res.get_next()
                relation_str = f"{s} → {label} → {o}"
                Logger.log(f"{relation_str:<40} | {imp:<6.1f} | {val:<6.1f} | {reason}")

            Logger.log("═"*80)
        except Exception as e:
            Logger.log(f"❌ DB 조회 실패: {e}")