import kuzu
import time
import numpy as np
from sentence_transformers import SentenceTransformer

class IrisMemory:
    def __init__(self, db_path="iris_brain_db"):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        # 로컬 경로에서 BGE-M3 로드
        self.embed_model = SentenceTransformer("./models/bge-m3") 
        # 망각 곡선 가중치 (작을수록 오래 기억함)
        self.decay_rate = 0.0001

    def start(self):
        self._prepare_schema()

    def stop(self):
        if self.conn:
            self.conn.close()
        self.db.close()

    def set_decay_rate(self, decay_rate):
        self.decay_rate = decay_rate

    def _prepare_schema(self):
        """DB 스키마 초기화 - 중복 생성 방지 처리"""
        try:
            self.conn.execute("CREATE NODE TABLE node (id STRING, embedding DOUBLE[], PRIMARY KEY (id))")
            self.conn.execute("""
                CREATE REL TABLE rel (
                    FROM node TO node, 
                    intensity DOUBLE, last_accessed DOUBLE, frequency INT64,
                    sub_label STRING, interpretation STRING,
                    MANY_MANY
                )
            """)
        except Exception:
            pass 

    def add_memory(self, triplets, state_delta):
        """새로운 기억(Triplets)을 그래프 DB에 각인"""
        # 감정 변화량의 절대값 합계를 기반으로 각인 강도 결정
        intensity = 0.5 + sum(abs(v) for v in state_delta.values() if isinstance(v, (int, float)))
        now = time.time()

        for t in triplets:
            subj, rel, obj = t['subject'], t['relation'], t['object']
            meta = t.get('metadata', {})
            
            # [수정] subject와 object 모두 임베딩 생성 (추후 검색 가능성 보장)
            subj_emb = self.embed_model.encode(subj).tolist()
            obj_emb = self.embed_model.encode(obj).tolist()
            
            # 1. 노드 MERGE (파라미터 바인딩으로 따옴표 에러 방지)
            self.conn.execute(
                "MERGE (n:node {id: $id}) SET n.embedding = $emb", 
                {"id": subj, "emb": subj_emb}
            )
            self.conn.execute(
                "MERGE (n:node {id: $id}) SET n.embedding = $emb", 
                {"id": obj, "emb": obj_emb}
            )

            # 2. 관계 MERGE - ON CREATE(최초 생성)와 ON MATCH(기존 업데이트) 구분
            self.conn.execute(f"""
                MATCH (s:node {{id: $subj}}), (o:node {{id: $obj}})
                MERGE (s)-[r:rel]->(o)
                ON CREATE SET 
                    r.intensity = $intensity,
                    r.frequency = 1,
                    r.last_accessed = $now,
                    r.sub_label = $label,
                    r.interpretation = $reason
                ON MATCH SET 
                    r.intensity = $intensity,
                    r.frequency = r.frequency + 1,
                    r.last_accessed = $now
            """, {
                "subj": subj, "obj": obj, "intensity": intensity, 
                "now": now, "label": meta.get('label', rel), 
                "reason": str(meta.get('reason', ''))
            })

    def retrieve_memory(self, query, top_k=5):
        """의미 유사도, 감정 강도, 망각 곡선을 결합한 고도화된 회상 로직"""
        query_emb = self.embed_model.encode(query).tolist()
        now = time.time()
        
        # 전체 관계망 스캔
        res = self.conn.execute("""
            MATCH (n:node)-[r:rel]->(o:node)
            RETURN n.id, o.id, r.intensity, r.frequency, r.last_accessed, r.sub_label, n.embedding
        """)

        candidates = []
        while res.has_next():
            row = res.get_next()
            subj, obj, intensity, freq, last_time, sub_label, node_emb = row
            
            # 코사인 유사도 계산
            sim = np.dot(query_emb, node_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(node_emb))
            
            # 유사도가 너무 낮으면(노이즈) 무시 (Threshold: 0.3)
            if sim < 0.3:
                continue

            # 망각 곡선 적용 (시간이 흐를수록 점수 하락)
            time_diff = now - last_time
            memory_strength = (intensity * freq) / (1 + self.decay_rate * time_diff)
            
            # 최종 점수 계산: 유사도와 기억 강도의 조화
            final_score = sim * memory_strength
            
            candidates.append({
                "score": final_score,
                "text": f"{subj} --({sub_label})--> {obj}",
                # 시스템 프롬프트의 [VIVID]/[FAINT] 지침과 동기화
                "intensity": "VIVID" if final_score > 0.7 else "FAINT" 
            })

        # 점수 순 정렬 및 상위 K개 반환
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return "\n".join([
            f"- [{c['intensity']}] {c['text']} (Score: {c['score']:.2f})" 
            for c in candidates[:top_k]
        ])

    def inspect_iris_brain(self):
        try:
            print(f"\n" + "═"*60)
            print(f"🧠 [Project Iris] 인지망(Cognitive Network) 정밀 진단")
            print("═"*60)

            # 1. 노드 분석 (인지 밀도 포함)
            nodes_res = self.conn.execute("MATCH (n:node) RETURN n.id")
            nodes = []
            while nodes_res.has_next():
                nodes.append(nodes_res.get_next()[0])
            
            print(f"📍 인지된 총 개체 수: {len(nodes)}개")
            print(f"   자산: {', '.join(nodes[:10])}{'...' if len(nodes) > 10 else ''}")

            # 2. 관계 분석 (망각 및 선명도 계산 포함)
            print("\n" + "─"*60)
            print(f"{'관계(Relation)':<30} | {'선명도':<6} | {'심리적 해석'}")
            print("─"*60)

            rels_res = self.conn.execute("""
                MATCH (s:node)-[r:rel]->(o:node) 
                RETURN s.id, r.sub_label, r.intensity, r.frequency, r.last_accessed, o.id, r.interpretation
            """)
            
            now = time.time()
            while rels_res.has_next():
                s, label, intensity, freq, last, o, reason = rels_res.get_next()
                
                # 망각 곡선을 고려한 현재 선명도 계산 (retrieve_memory 로직과 동기화)
                time_diff = now - last
                current_strength = (intensity * freq) / (1 + 0.0001 * time_diff)
                vividness = "VIVID" if current_strength > 0.7 else "FAINT"
                
                relation_str = f"{s} → {label} → {o}"
                print(f"{relation_str:<30} | {vividness:<6} | {reason}")

            print("═"*60)

        except Exception as e:
            print(f"❌ DB 조회 실패: {e}")