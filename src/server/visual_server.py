import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.append(project_root)

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sim.iris_memory import IrisMemory
import uvicorn

app = FastAPI()
memory = IrisMemory(db_path="../brain_db/[IRIS]_brain", load_embed_model=False)

@app.get("/api/brain")
async def get_brain():
    return memory.get_visual_data()

@app.get("/", response_class=HTMLResponse)
async def read_index():
    index_path = os.path.join(current_dir, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()

@app.on_event("shutdown")
def shutdown_event():
    memory.stop()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
