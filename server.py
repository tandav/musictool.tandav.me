from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from musictool import config
from musictool.chord import SpecificChord
from musictool.note import SpecificNote
from musictool.scale import Scale
from musictool.scale import ComparedScales
from musictool.scale import all_scales
from musictool.scale import majors
from musictool.noteset import NoteRange
from html_table import midi_table_html

scale = Scale.from_name('C', 'major')
noterange = NoteRange('C2', 'C4', noteset=scale)
lowest = SpecificNote.from_str('C1')

chromatic_notes_set = set(config.chromatic_notes)

# static_folder = Path(__file__).parent / 'static'
static_folder = Path('static')
# print(static_folder.exists())

app = FastAPI()
app.mount("/static/", StaticFiles(directory=static_folder), name="static")


@app.get("/scale_not_found", response_class=HTMLResponse)
def scale_not_found():
    return '''
    <header><a href='/'>home</a></header>
    <h1>404: scale not found</h1>
    '''


@app.get("/play_chord/{chord}")
async def play_chord(chord: str):
    print('PLAYIN CHORD', chord)
    # notes = tuple(SpecificNote(n, octave=5) for n in chord)
    # raise NotImplementedError('REWRITE: instead of rely on 1st note explicitly pass root CEG_C')
    # await SpecificChord(frozenset(notes), root=notes[0]).play(bass=-1)
    await SpecificChord.from_str(chord).play(seconds=1)
    return {'status': 'play_chord success'}


@app.get("/play_note/{note}/{octave}")
async def play_note(note: str, octave: int):
    print('PLAYIN NOTE', note, octave)
    await SpecificNote(note, octave).play()
    return {'status': 'play_note success'}


@app.get("/", response_class=HTMLResponse)
async def root(): return RedirectResponse('/circle/diatonic/')


@app.get("/favicon.ico", response_class=HTMLResponse)
async def favicon(): return FileResponse(static_folder / 'favicon.ico')


@app.get("/available_scales", response_class=HTMLResponse)
async def available_scales():
    html = '<h1>Available scales for circle of fifths</h1>'
    return html + '\n'.join(f"<a href='/circle/{k}/'>/circle/{k}/</a><br>" for k in majors.keys())




# @app.get("/diads", response_class=HTMLResponse)
# async def diads_root():
#     return RedirectResponse(f'/diads/lowest/{lowest}')


@app.get('/diads/lowest_up')
async def diads_lowest_up():
    global lowest
    lowest = scale.add_note(lowest, 1)
    print(lowest)
    # return diads()
    return RedirectResponse('/diads')


@app.get('/diads/lowest_down')
async def diads_lowest_down():
    global lowest
    lowest = scale.add_note(lowest, -1)
    print(lowest)
    # return diads()
    return RedirectResponse('/diads')


@app.get("/diads", response_class=HTMLResponse)
async def diads():
    lines = []
    for row_note in noterange:
        lines.append('<tr>')
        for col_note in noterange:
            chord = SpecificChord(frozenset({lowest, row_note, col_note}))
            td_classes = set()

            if col_note.abstract == 'C':
                td_classes.add('C_col')
            if row_note.abstract == 'C':
                td_classes.add('C_row')
            if len(chord) == 3 and chord[2] - chord[1] >= 12:
                td_classes.add('greyed')
            if row_note < col_note:
                td_classes.add('greyed')

            if 'greyed' not in td_classes:
                scale_ = scale.note_scales[col_note.abstract]
                td_classes.add(scale_)
                # assert row_note <= col_note, (row_note, col_note, i, j)
            #     sertionError: (D2, C2, 1, 0)

            td_classes = f"class='{' '.join(td_classes)}'" if td_classes else ''
            lines.append(f"    <td {td_classes}onclick=play_chord('{chord}')>{chord}</td>")
        lines.append('</tr>')
    table_data = '\n'.join(lines)

    "< span class ='chord_button {chord.name} {is_shared}' onclick=play_chord('{chord.str_chord}') > {i} < / span >"

    html = f'''
    <h1>diads table {lowest}</h1>
    <a href='/diads/lowest_down'>lowest_down</a>
    <a href='/diads/lowest_up'>lowest_up</a>
    <table>
    <tbody>
    </tbody>
    
    {table_data}
    </table>
    '''
    background_color = scale.note_scales[lowest.abstract]

    css = '''
    <style>
        :root {
        --major: #FFFFFF;
        --dorian: #54E346;
        --phrygian: #00FFCC;
        --lydian: #68A6FC;
        --mixolydian: #FFF47D;
        --minor: #D83A56;
        --locrian: #B980F0;
    }
    
    body {
        font-family: 'SF Mono';
    }

    table, td {
        font-size: 0.8em;
        border: 1px solid #dddddd;
    }
    
    td {
        width: 50px;
        height: 50px;
    }
    
    td.C_col {
        border-left: 1px solid black;
    }
    
    td.C_row {
        border-top: 1px solid black;
    }


    th {
        writing-mode: vertical-lr;
        max-height: 100px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .major { background-color: var(--major); }
    .dorian { background-color: var(--dorian); }
    .phrygian { background-color: var(--phrygian); }
    .lydian { background-color: var(--lydian); }
    .mixolydian { background-color: var(--mixolydian); }
    .minor { background-color: var(--minor); }
    .locrian { background-color: var(--locrian); }
    
    td.greyed {
        color: rgba(0, 0, 0, 0.1);
        background-color: rgba(0, 0, 0, 0.1);
    }
    </style>
    '''

    # <script src="/static/ui.js"></script>


    return f'''
    <html>
    <head>
    <script src="/static/play.js"></script>
    </head>
    <body class='{background_color}'>
    {html}
    {css}
    </body>
    ''' + '''
    <script src="/static/ui.js"></script>
    '''
