from faststream import FastStream, Depends
from faststream.kafka import KafkaBroker
from worker.models import UserTag
from worker.db import AnalyticsDAO
from functools import cache

broker = KafkaBroker("st117vm104.rtb-lab.pl:9092")

app = FastStream(broker)

@cache
def get_db():
    return AnalyticsDAO()

@broker.subscriber("user-tags")
async def handle_msg(tag: UserTag, dao: AnalyticsDAO = Depends(get_db)):
    dao.increment_all(tag)