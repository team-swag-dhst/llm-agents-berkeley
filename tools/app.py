from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
import uvicorn

class SearchRequest(BaseModel):
    query: str

class ReadUrlRequest(BaseModel):
    url: str

load_dotenv()

app = FastAPI()

@app.post("/search")
def search(request: SearchRequest):
    url = f"https://s.jina.ai/{quote_plus(request.query)}"
    headers = {"Authorization": f"Bearer {os.environ['JINAI_API_KEY']}"}

    response = requests.get(url, headers=headers)
    return response.text

@app.post("/read_url")
def read_url(request: ReadUrlRequest):
    url = f"https://r.jina.ai/{request.url}"
    headers = {"Authorization": f"Bearer {os.environ['JINAI_API_KEY']}"}
    response = requests.get(url, headers=headers)
    return response.text

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
