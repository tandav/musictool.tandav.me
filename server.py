import asyncio
import mido
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from musictool.note import SpecificNote
from musictool.chord import SpecificChord
from musictool.chord import Chord
from musictool.scale import Scale
from musictool.noterange import NoteRange
from musictool.piano import Piano
from musictool import config

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
        
        <div>scale: <span id='scale'></span></div>
        <div>chord: <span id='chord'></span></div>
        <div>chord_abstract: <span id='chord_abstract'></span></div>
        <div>possibilities: <span id='possibilities'></span></div>
        <div>chord_step: <span id='chord_step'></span></div>
        
        <h2>piano</h2>
        <div id='piano'></div>
        
        <script>
            var client_id = Date.now()
            let i = 0
            const n = 10
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8001/ws/${client_id}`);
            ws.onmessage = function(event) {
                var data = JSON.parse(event.data);
                console.log(data)
                // console.log(data['message'])
                // var messages = document.getElementById('messages')
                // var message = document.createElement('li')
                // var content = document.createTextNode(event.data)
                // message.appendChild(content)
                // messages.appendChild(message)
                i += 1
                // console.log(i)
                document.getElementById('scale').textContent = data['scale']
                document.getElementById('chord').textContent = data['chord']
                document.getElementById('chord_abstract').textContent = data['chord_abstract']
                document.getElementById('possibilities').textContent = data['possibilities']
                document.getElementById('chord_step').textContent = data['chord_step']
                document.getElementById('piano').innerHTML = data['piano']
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

css = '''
<style>
body {
    font-family: SFMono, monospace;
}
</style>
'''


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: object):
        for connection in self.active_connections:
            print({k: v for k, v in message.items() if k != 'piano'})
            await connection.send_json(message)



manager = ConnectionManager()

port = mido.open_input('IAC Driver Bus 1')
playing_notes = set()
# scale = Scale.from_name('C', 'major')
scale = Scale.from_name('F', 'minor')


def chord_to_html(chord: SpecificChord) -> str:
    piano = Piano(
        note_colors=dict.fromkeys(chord.notes, config.RED),
        squares={note: {'text': str(note), 'text_size': '8'} for note in chord},
        noterange=NoteRange(SpecificNote('C', 2), SpecificNote('C', 10))
    )._repr_svg_()
    return f"""
    <div class='specificchord'>
    <h3 style='height:1em;' class='card_header'>{chord!r}</h3>
    {piano}
    </div>
    """

def sync_receive_midi_and_broadcast():
    # messages = []
    messages = list(port.iter_pending())
    if not messages:
        return
    for msg in messages:
        # if msg.type not in {'note_on', 'note_off'}:
        #     continue

        if msg.type == 'note_on':
            playing_notes.add(SpecificNote.from_absolute_i(msg.note))
        elif msg.type == 'note_off':
            playing_notes.remove(SpecificNote.from_absolute_i(msg.note))
        else:
            continue
        # note = SpecificNote.from_absolute_i(msg.note)
        # msg_str = f'{note} {msg.type}'
        # messages.append(msg_str)
    return SpecificChord(frozenset(playing_notes))


async def receive_midi_and_broadcast(manager: ConnectionManager):
    loop = asyncio.get_running_loop()
    while True:
        # messages = await loop.run_in_executor(None, sync_receive_midi_and_broadcast)
        chord = await loop.run_in_executor(None, sync_receive_midi_and_broadcast)
        if chord is None:
            continue

        possibilities = []
        abstract = chord.abstract

        for note in abstract:
            possibilities.append(Chord(abstract.notes, root=note))

        await manager.broadcast({
            'scale': str(scale),
            'chord': f'{chord}',
            'chord_abstract': f'{chord.abstract}',
            'possibilities': f'{possibilities}',
            'chord_step': 'chord_step',
            'piano': chord_to_html(chord),
        })

@app.on_event("startup")
async def startup_event() -> None:
    asyncio.create_task(receive_midi_and_broadcast(manager))


@app.get("/")
async def get():
    return HTMLResponse(html + css)


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")



