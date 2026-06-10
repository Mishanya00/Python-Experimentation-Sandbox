from faststream import FastStream
from faststream.rabbit import RabbitBroker


rabbit_url = "amqp://rabbitmq:rabbitmq@localhost:5673/"

broker = RabbitBroker(rabbit_url)

app = FastStream(broker)


@broker.subscriber("test.queue")
async def handle(name: str, age: int):
    print(f"{name=}, {age=}")


@app.after_startup
async def t():
    await broker.publish(
        {
            "name": "John",
            "age": 25,
            "useless": {
                "nested": "useless"
            },
        }, 
        queue="test.queue",
    )