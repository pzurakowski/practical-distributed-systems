from fastapi import FastAPI, Query, Depends
from pydantic import BaseModel
from typing import Literal, List, Annotated, Union, Dict
from functools import cache
from datetime import datetime

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

@cache
def profile_store():
    return {}

@app.post("/user_tags", status_code=204)
async def user_tags(user_tag: UserTag, store: Annotated[Dict[str, UserProfile], Depends(profile_store)]):
    cookie = user_tag.cookie
    
    if cookie not in store:
        store[cookie] = UserProfile(cookie=cookie, views=[], buys=[])

    if user_tag.action == "VIEW":
        store[cookie].views.append(user_tag)
        if len(store[cookie].views) > 200:
            store[cookie].views.pop(0)
    elif user_tag.action == "BUY":
        store[cookie].buys.append(user_tag)
        if len(store[cookie].buys) > 200:
            store[cookie].buys.pop(0)


@app.post("/user_profiles/{cookie}", status_code=200)
async def user_profiles(cookie: str, time_range: str, body: UserProfile, store: Annotated[Dict[str, UserProfile], Depends(profile_store)], limit: int = 200):
    profile = store.get(cookie)

    if profile is None:
        print("No profile found")
        return UserProfile(cookie=cookie, views=[], buys=[])

    start_time_str, end_time_str = time_range.split('_')
    start_time = datetime.fromisoformat(start_time_str)
    end_time = datetime.fromisoformat(end_time_str)

    filtered_views = [
        view for view in profile.views
        if start_time <= datetime.fromisoformat(view.time[:-1]) < end_time
    ]

    filtered_buys = [
        buy for buy in profile.buys
        if start_time <= datetime.fromisoformat(buy.time[:-1]) < end_time
    ]

    result = UserProfile(cookie=cookie, views=filtered_views[-limit:], buys=filtered_buys[-limit:])

    if result != body:
        print("Profile mismatch")
        print(f"Expected: {body}")
        print(f"Actual: {result}")

    return result

@app.post("/aggregates")
async def aggregates(time_range: str, action: Literal["VIEW", "BUY"], body: Aggregate, aggregates: Annotated[Union[List[Literal["COUNT", "SUM_PRICE"]], None], Query()] = None, origin: str | None = None, brand_id: str | None = None, category_id: str | None = None):
    return body