from fastapi import FastAPI, Query, Depends
from typing import Literal, List, Annotated, Union, Dict
from datetime import datetime
from front.models import UserTag, UserProfile, Aggregate
from front.db import UserProfileDAO
from functools import cache
from kafka import KafkaProducer
import time

app = FastAPI()

time.sleep(10)

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: v.model_dump_json().encode('utf-8')
)

@cache
def get_db():
    db = UserProfileDAO()
    return db

@app.post("/user_tags", status_code=204)
async def user_tags(user_tag: UserTag, dao: Annotated[Dict[str, UserProfile], Depends(get_db)]):
    dao.add_tag(user_tag)

    producer.send('user-tags', user_tag)

@app.post("/user_profiles/{cookie}", status_code=200)
async def user_profiles(cookie: str, time_range: str, body: UserProfile, dao: Annotated[Dict[str, UserProfile], Depends(get_db)], limit: int = 200):
    profile = dao.get(cookie)

    if profile is None:
        return UserProfile(cookie=cookie, views=[], buys=[])

    start_time_str, end_time_str = time_range.split('_')
    start_time = datetime.fromisoformat(start_time_str)
    end_time = datetime.fromisoformat(end_time_str)

    filtered_views = [
        view for view in profile.views
        if start_time <= datetime.fromisoformat(view.time[:-1]) < end_time
    ]
    filtered_views.reverse()

    filtered_buys = [
        buy for buy in profile.buys
        if start_time <= datetime.fromisoformat(buy.time[:-1]) < end_time
    ]
    filtered_buys.reverse()

    result = UserProfile(cookie=cookie, views=filtered_views[:limit], buys=filtered_buys[:limit])

    return result

@app.post("/aggregates")
async def aggregates(time_range: str, action: Literal["VIEW", "BUY"], body: Aggregate, aggregates: Annotated[Union[List[Literal["COUNT", "SUM_PRICE"]], None], Query()] = None, origin: str | None = None, brand_id: str | None = None, category_id: str | None = None):
    return body