from typing import Annotated

from pydantic import Field, NonNegativeInt

from faststream import FastStream
from faststream.rabbit import RabbitBroker


rabbit_url = "amqp://rabbitmq:rabbitmq@localhost:5673/"

broker = RabbitBroker(rabbit_url)
app = FastStream(broker)


@broker.subscriber("test.queue")
async def handle(
    name: Annotated[str, Field(..., examples=["John"], description="Registered user name")],
    user_id: Annotated[NonNegativeInt, Field(..., examples=[1], description="Registered user id")],
):
    assert name == "Mozeratti"

    assert user_id == 111


@app.after_startup
async def t():
    await broker.publish(
        {
            "name": "Mozeratti",
            "user_id": 111,
        }, 
        queue="test.queue",
    )

    await broker.publish(
        {
            "name": "Mozeratti",
            "user_id": -1,
        }, 
        queue="test.queue",
    )

    await broker.publish(
        {
            "name": "Josh Makkenzi",
            "user_id": 111,
        }, 
        queue="test.queue",
    )