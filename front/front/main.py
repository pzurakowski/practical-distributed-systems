from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Literal, List, Annotated, Union

app = FastAPI()

class ProductInfo(BaseModel):
    product_id: int
    brand_id: str
    category_id: str
    price: int

class UserTag(BaseModel):
    time: str
    cookie: str
    country: str
    device: Literal["PC", "MOBILE", "TV"]
    action: Literal["VIEW", "BUY"]
    origin: str
    product_info: ProductInfo

class UserProfile(BaseModel):
    cookie: str
    views: List[UserTag]
    buys: List[UserTag]

class Aggregate(BaseModel):
    columns: List[str]
    rows: List[List[str]]

@app.post("/user_tags", status_code=204)
async def user_tags(user_tag: UserTag):
    return

@app.post("/user_profiles/{cookie}", status_code=200)
async def user_profiles(cookie: str, time_range: str, body: UserProfile, limit: int = 200):
    return body

@app.post("/aggregates")
async def aggregates(time_range: str, action: Literal["VIEW", "BUY"], body: Aggregate, aggregates: Annotated[Union[List[Literal["COUNT", "SUM_PRICE"]], None], Query()] = None, origin: str | None = None, brand_id: str | None = None, category_id: str | None = None):
    return body