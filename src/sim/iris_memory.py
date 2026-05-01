import kuzu
import time
import numpy as np
from sentence_transformers import SentenceTransformer

class IrisMemory:
    """
    KuzuDB의 표준 MERGE 문법을 사용하는 순수 인지 엔진.
    에러의 원인이었던 FOREACH를 제거하고 가독성을 높였습니다.
    """
    def __init__(self, db_path="iris_brain_db"):
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
        self.embed_model = SentenceTransformer("./models/bge-m3") 
        self.decay_rate = 0.0001

    def start(self):
        self._prepare_schema()

    def stop(self):
        self.conn.close()
        self.conn = None
        self.db.close()
        self.db = None
        self.embed_model = None

    def _prepare_schema(self):
        """DB 스키마 초기화"""
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
        """
        [수정] MERGE ... ON CREATE / ON MATCH 문법을 사용하여 
        관계의 생성과 업데이트를 한 번에 처리합니다.
        """
        intensity = 0.5 + sum(abs(v) for v in state_delta.values() if isinstance(v, (int, float)))
        now = time.time()

        for t in triplets:
            subj, rel, obj = t['subject'], t['relation'], t['object']
            meta = t.get('metadata', {})
            embedding = self.embed_model.encode(subj).tolist()
            
            # 1. 노드 생성 및 벡터 저장
            self.conn.execute(f"MERGE (n:node {{id: '{subj}'}}) SET n.embedding = $emb", {"emb": embedding})
            self.conn.execute(f"MERGE (n:node {{id: '{obj}'}})")

            # 2. [핵심 수정] 관계 MERGE (FOREACH 대신 표준 문법 사용)
            # 관계가 없으면 CREATE 시점을 실행하고, 있으면 MATCH 시점을 실행합니다.
            self.conn.execute(f"""
                MATCH (s:node {{id: '{subj}'}}), (o:node {{id: '{obj}'}})
                MERGE (s)-[r:rel]->(o)
                ON CREATE SET 
                    r.intensity = {intensity},
                    r.frequency = 1,
                    r.last_accessed = {now},
                    r.sub_label = '{meta.get('label', rel)}',
                    r.interpretation = '{str(meta.get('reason', '')).replace("'", "''")}'
                ON MATCH SET 
                    r.intensity = {intensity},
                    r.frequency = r.frequency + 1,
                    r.last_accessed = {now}
            """)

    def retrieve_memory(self, query, top_k=5):
        """의미 유사도와 심리적 가중치를 결합한 회상 로직"""
        query_emb = self.embed_model.encode(query).tolist()
        now = time.time()
        
        # 전체 관계망을 훑으며 후보군 추출
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
            
            # 망각 곡선 적용 (시간이 흐를수록 약해짐)
            time_diff = now - last_time
            memory_strength = (intensity * freq) / (1 + self.decay_rate * time_diff)
            
            # 사실 관계를 기반으로 하고 싶다면 final_score = (sim ** 2) * memory_strength
            # 감정적 강도를 기반으로 하고 싶다면 final_score = sim * (memory_strength ** 2)
            # 감정적 강도와 사실 관계를 결합하고 싶다면 final_score = sim * memory_strength
            final_score = sim * memory_strength
            candidates.append({
                "score": final_score,
                "text": f"{subj} --({sub_label})--> {obj}",
                "intensity": "VIVID" if final_score > 0.6 else "FAINT"
            })

        candidates.sort(key=lambda x: x['score'], reverse=True)
        return "\n".join([f"- [{c['intensity']}] {c['text']} (Score: {c['score']:.2f})" for c in candidates[:top_k]])

    def inspect_iris_brain(self, db_path="iris_brain_db"):
        try:
            # 1. DB 연결
            print(f"\n" + "="*50)
            print(f"🧠 아이리스 신경망 상태 점검: {db_path}")
            print("="*50)

            # 2. 노드(node) 조회 - 아이리스가 인지한 주체들
            print("\n[1. 인지된 개체 (Nodes)]")
            nodes_res = self.conn.execute("MATCH (n:node) RETURN n.id")
            node_count = 0
            while nodes_res.has_next():
                row = nodes_res.get_next()
                print(f"📍 ID: {row[0]}")
                node_count += 1
            
            if node_count == 0:
                print("비어 있음: 아직 각인된 기억이 없습니다.")

            # 3. 관계(rel) 조회 - 기억의 파편과 심리 수치
            print("\n[2. 연결된 기억과 심리 수치 (Relationships)]")
            # intensity, sub_label, frequency 등을 한눈에 확인
            rels_res = self.conn.execute("""
                MATCH (s:node)-[r:rel]->(o:node) 
                RETURN s.id, r.sub_label, r.intensity, r.frequency, r.last_accessed, o.id, r.interpretation
            """)
            
            rel_count = 0
            while rels_res.has_next():
                s_id, label, intensity, freq, last, o_id, reason = rels_res.get_next()
                
                print(f"🔗 {s_id} --({label})--> {o_id}")
                print(f"   └ 강도: {intensity:.2f} | 빈도: {freq}회 | 해석: {reason}")
                rel_count += 1
                
            if rel_count == 0:
                print("비어 있음: 형성된 관계가 없습니다.")

            print("\n" + "="*50)
            print(f"총 {node_count}개의 개체와 {rel_count}개의 기억 파편이 발견되었습니다.")
            print("="*50)

        except Exception as e:
            print(f"❌ DB 조회 실패: {e}")