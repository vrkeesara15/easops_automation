from fastapi import FastAPI
from langgraph.graph import StateGraph

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}