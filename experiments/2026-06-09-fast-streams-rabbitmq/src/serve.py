from faststream import FastStream
from faststream.rabbit import RabbitBroker


broker = RabbitBroker("amqp://rabbitmq:rabbitmq@localhost:5672/")

app = FastStream(broker)


@broker.subscriber("test")
async def base_handler(body):
    print(body)
