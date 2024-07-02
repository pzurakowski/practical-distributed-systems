from faststream import FastStream
from faststream.kafka import KafkaBroker
from worker.models import UserTag

broker = KafkaBroker("kafka:9092")

app = FastStream(broker)

@broker.subscriber("user-tags")
async def handle_msg(tag: UserTag):
    print(f"Got tag: {tag}")