# run.py

import logging
import os
import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from ..apis.channel_register import register_apis_router
from ..apis.health import health_apis_router
from ..apis.chat import chat_apis_router
from ..chat_app.dependency_setup import whatsapp_client

# ✨ FIX: Import the listener module with an alias for clarity
from . import listner as pubsub_listener

# This global is not strictly necessary anymore but doesn't hurt
subscriber_task = None


asyncio.get_event_loop().set_debug(True)
def create_app():
    """
    Creates and F.

    Returns:
        Flask: A configured FastAPI application instance.
    """

    app = FastAPI(lifespan=lifespan)
    app.include_router(register_apis_router)
    app.include_router(health_apis_router)
    app.include_router(chat_apis_router)
    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    pid = os.getpid()
    print(f"FastAPI app is running with PID: {pid}")
    
    # ✨ FIX: Get the running event loop and pass it to the listener module
    loop = asyncio.get_running_loop()
    pubsub_listener.main_loop = loop

    # Create the background task to listen for messages
    global subscriber_task
    subscriber_task = asyncio.create_task(pubsub_listener.listen_for_messages())
    
    yield

    await whatsapp_client._close()

    # Cleanly shut down the subscriber task and client
    if subscriber_task:
        subscriber_task.cancel()
    await pubsub_listener.cancel()
    print("Closed all clients.")

app = create_app()

if __name__ == '__main__':
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=4000
    )