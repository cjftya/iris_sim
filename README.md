# iris_sim

## 모델 다운로드
# 1. 모델 폴더 생성
mkdir -p models

# 2. Hugging Face 리포지토리 클론
git clone https://huggingface.co/BAAI/bge-m3 models/bge-m3

# 3. 불필요한 대용량 파일 정리 (선택 사항)
cd models/bge-m3
rm -rf .git