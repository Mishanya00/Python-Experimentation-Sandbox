import pytest
from pydantic import ValidationError
from faststream.rabbit import RabbitBroker, TestRabbitBroker


rabbit_url = "amqp://rabbitmq:rabbitmq@localhost:5673/"

broker = RabbitBroker(rabbit_url)


@broker.subscriber("test-queue")
async def handle(msg: str) -> None:
    raise ValueError


@pytest.mark.asyncio()
async def test_handle() -> None:
    async with TestRabbitBroker(broker) as br:
        with pytest.raises(ValueError):
            await br.publish("hello!", "test-queue")


@pytest.mark.asyncio
async def test_handle() -> None:
    async with TestRabbitBroker(broker, with_real=True) as br:
        await br.publish({"name": "John", "user_id": 1}, queue="test-queue")
        await handle.wait_call(timeout=3)
        handle.mock.assert_called_once_with({"name": "John", "user_id": 1})

    
assert not handle.mock.called  # mock is reset

@pytest.mark.asyncio
async def test_validation_error() -> None:
    async with TestRabbitBroker(broker, with_real=True) as br:
        with pytest.raises(ValidationError):        
            await br.publish("wrong message", queue="test-queue")
            await handle.wait_call(timeout=3)

        
        handle.mock.assert_called_once_with("wrong message")
