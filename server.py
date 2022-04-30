import asyncio
import mido
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from musictool.note import SpecificNote


app = FastAPI()


html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Midi Server</title>
    </head>
    <body>
        <h1>WebSocket Midi Server</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        
        <h3>scale: <span id='scale'></span></h3>
        <h3>chord: <span id='chord'></span></h3>
        <h3>chord_step: <span id='chord_step'></span></h3>
        <h3>message: <span id='message'></span></h3>
        
        <script>
            var client_id = Date.now()
            let i = 0
            const n = 10
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8001/ws/${client_id}`);
            ws.onmessage = function(event) {
                var data = JSON.parse(event.data);
                console.log(data)
                console.log(data['message'])
                // var messages = document.getElementById('messages')
                // var message = document.createElement('li')
                // var content = document.createTextNode(event.data)
                // message.appendChild(content)
                // messages.appendChild(message)
                i += 1
                // console.log(i)
                document.getElementById('scale').textContent = data['scale']
                document.getElementById('chord').textContent = data['chord']
                document.getElementById('chord_step').textContent = data['chord_step']
                document.getElementById('message').textContent = data['message']
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


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: object):
        print('broadcast', message)
        for connection in self.active_connections:
            await connection.send_json(message)



manager = ConnectionManager()

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
            await manager.broadcast({
                'scale': 'scale',
                'chord': 'chord',
                'chord_step': 'chord_step',
                'message': message,
            })

@app.on_event("startup")
async def startup_event() -> None:
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



