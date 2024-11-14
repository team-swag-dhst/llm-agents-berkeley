from pydantic import BaseModel, Field
import requests
from urllib.parse import quote_plus
import os
import logging

class SearchInternet(BaseModel):
    """Search the internet given a query. Response is returned as a string."""
    query: str = Field(description="The query to search the internet for.", max_length=100)


class ReadWebsite(BaseModel):
    """Read the content of a website given a URL. Response is returned as a string."""
    url: str

def search(request: SearchInternet):
    url = f"https://s.jina.ai/{quote_plus(request.query)}"
    headers = {"Authorization": f"Bearer {os.environ['JINAI_API_KEY']}"}
    response = requests.get(url, headers=headers)

    logging.info(response.text[0:100])

    return response.text

def read(request: ReadWebsite):
    url = f"https://r.jina.ai/{request.url}"
    headers = {"Authorization": f"Bearer {os.environ['JINAI_API_KEY']}"}
    response = requests.get(url, headers=headers)

    return response.text
