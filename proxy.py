from typing import Annotated
from fastapi import FastAPI, Request, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()
security = HTTPBasic()


@app.post("/{path:path}")
async def proxy(request: Request, path: str, credentials: Annotated[HTTPBasicCredentials, Depends(security)]):
    url = f"https://{path}"
    body = await request.json()
    print(body)
    response = requests.post(
        url,
        params=request.query_params,
        auth=(credentials.username, credentials.password),
        data=body)
    print(response.json())
    return HTMLResponse(content=response.text, status_code=response.status_code)
