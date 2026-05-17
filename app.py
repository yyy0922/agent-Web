from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import shutil
import os
from pathlib import Path

from ingest import ingest_file
from retriever import answer_question

app = FastAPI(title="Multimodal Document QA")

DATA_DIR = Path("./data")
DATA_DIR.mkdir(exist_ok=True)


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/ingest")
async def ingest(upload_file: UploadFile = File(...)):
    dest = DATA_DIR / upload_file.filename
    try:
        with open(dest, "wb") as f:
            shutil.copyfileobj(upload_file.file, f)
    finally:
        upload_file.file.close()
    # process file (sync work for simplicity)
    try:
        ingest_file(str(dest))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return JSONResponse({"status": "ingested", "file": upload_file.filename})


@app.post("/query")
async def query(payload: dict):
    question = payload.get("question")
    if not question:
        raise HTTPException(status_code=400, detail="question required")
    resp = answer_question(question)
    return JSONResponse(resp)
