import asyncio
import string
import random
import os
from collections import deque
from threading import Event
from threading import Thread

import mido
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from musictool.note import SpecificNote


class MidiServer(Thread):
    def __init__(self, manager):
        super().__init__()
        self.port = mido.open_input('IAC Driver Bus 1')
        self.queue = deque(maxlen=20)
        self.manager = manager

    def run(self) -> None:
        for msg in self.port:
            if msg.type not in {'note_on', 'note_off'}:
                continue
            note = SpecificNote.from_absolute_i(msg.note)
            msg_str = f'{note} {msg.type}'
            self.manager.broadcast(msg_str)
            # self.queue.append(msg_str)


app = FastAPI()


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8001/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""
from fastapi.concurrency import run_in_threadpool


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        print('broadcast', message)
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()
# midi_server = MidiServer(manager)
# midi_server.start()

port = mido.open_input('IAC Driver Bus 1')
def sync_receive_midi_and_broadcast():
    messages = []
    for msg in port.iter_pending():
        if msg.type not in {'note_on', 'note_off'}:
            continue
        note = SpecificNote.from_absolute_i(msg.note)
        msg_str = f'{note} {msg.type}'
        messages.append(msg_str)
    return messages


async def receive_midi_and_broadcast(manager: ConnectionManager):
    loop = asyncio.get_running_loop()
    while True:
        messages = await loop.run_in_executor(None, sync_receive_midi_and_broadcast)
        for message in messages:
            await manager.broadcast(message)

@app.on_event("startup")
async def startup_event() -> None:
    """tasks to do at server startup"""
    # asyncio.create_task(Gatherer().start_metering_daemon())
    asyncio.create_task(receive_midi_and_broadcast(manager))


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")

    # else:  # secondary/read only connections
    #     pass

# for msg in port.iter_pending():
#     if msg.type not in {'note_on', 'note_off'}:
#         continue
#     note = SpecificNote.from_absolute_i(msg.note)
#     await websocket.send_text(str(note))

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#
#     try:
#         # for msg in port.iter_pending():
#         for msg in port:
#             if msg.type not in {'note_on', 'note_off'}:
#                 continue
#             note = SpecificNote.from_absolute_i(msg.note)
#             await websocket.send_text(str(note))
#     except WebSocketDisconnect:

    # while True:
        # data = await websocket.receive_text()
        # await websocket.send_text(f"Message text was: {data}")

        # await websocket.send_text(''.join(random.sample(string.ascii_lowercase, 8)))
        # await asyncio.sleep(1)


