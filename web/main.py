from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from config import API_KEYS
from tasks import pair_launch


app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def api_key_auth(api_key: str = Depends(oauth2_scheme)) -> None:
    if api_key not in API_KEYS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Forbidden")


@app.get('/api/test/')
async def test():
    return {"status": "ok"}


@app.get("/api/scrapingPair/bet99-smarkets/{sheet_name}", dependencies=[Depends(api_key_auth)])
async def scraping_bet99_smarkets(sheet_name: str):
    # TODO: add the ability to check running tasks for this pair so as not to run a task with each request
    pair_launch.delay(
        sheet_name=sheet_name,
        exchange='smarkets',
        bookmaker='bet99',
        save_from_redis=True
    )
    return {"status": "ok"}

