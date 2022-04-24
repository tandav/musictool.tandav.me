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

noterange = NoteRange('C2', 'C4', noteset=Scale.from_name('C', 'major'))

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


@app.get("/circle/{kind}/", response_class=HTMLResponse)
async def circle_diatonic(kind: str):
    if (majors_:= majors.get(kind)) is None:
        return RedirectResponse('/available_scales')

    html = ''
    for i, scale in enumerate(majors_, start=1):
        html += scale.with_html_classes(('kinda_circle', f'_{i}'))

    return f'''\
    <link rel="stylesheet" href="/static/circle.css">
    <link rel="stylesheet" href="/static/main.css">
    <script src="/static/play.js"></script>
    <div class='container'>{html}</div>
    '''


@app.get("/circle/{kind}/{selected_major}", response_class=HTMLResponse)
async def circle_selected(kind: str, selected_major: str):
    # workaround, maybe refactor this later
    m = {
        'diatonic': 'major',
        'harmonic': 'h_major',
        'melodic': 'm_major',
        'pentatonic': 'p_major',
        'sudu': 's_major',
    }.get(kind)
    if m is None:
        return RedirectResponse('/available_scales')
    html = ''
    selected = all_scales[kind][selected_major, m]
    for i, scale in enumerate(majors[kind], start=1):
        if scale == selected:
            html += ComparedScales(selected, scale).with_html_classes(('kinda_circle', f'_{i}', 'selected_scale'))
        else:
            html += ComparedScales(selected, scale).with_html_classes(('kinda_circle', f'_{i}'))

    return f'''\
    <link rel="stylesheet" href="/static/circle.css">
    <link rel="stylesheet" href="/static/main.css">
    <script src="/static/play.js"></script>
    <div class='container'>{html}</div>
    '''


@app.get("/circle")
async def circle(): return RedirectResponse('/circle/diatonic')


# @app.get("/midi_piano", response_class=HTMLResponse)
# async def midi_piano(): return midi_piano_html()


@app.get("/midi_table", response_class=HTMLResponse)
async def midi_table(): return midi_table_html()


@app.get("/diads", response_class=HTMLResponse)
async def diads():
    lines = []
    for i, row_note in enumerate(noterange):
        lines.append('<tr>')
        for j, col_note in enumerate(noterange):
            chord = SpecificChord(frozenset({row_note, col_note}))
            td_classes = []
            if len(chord) > 1 and chord[-1] - chord[0] >= 12:
                td_classes.append('big_interval')
            if col_note.abstract == 'C':
                td_classes.append('C_col')
            if row_note.abstract == 'C':
                td_classes.append('C_row')
            if j > i:
                td_classes.append('upper_triangle')
            td_classes = f"class='{' '.join(td_classes)}'" if td_classes else ''
            lines.append(f"    <td {td_classes}onclick=play_chord('{chord}')>{chord}</td>")
        lines.append('</tr>')
    table_data = '\n'.join(lines)

    "< span class ='chord_button {chord.name} {is_shared}' onclick=play_chord('{chord.str_chord}') > {i} < / span >"

    html = f'''
    <script src="/static/play.js"></script>
    <h1>diads table</h1>
    <table>
    <tbody>
    </tbody>
    
    {table_data}
    </table>
    '''

    css = '''
    <style>
    body {
        font-family: 'SF Mono';
    }

    table, td {
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
    td.upper_triangle {
        color: rgba(0, 0, 0, 0.1);
    }

    th {
        writing-mode: vertical-lr;
        max-height: 100px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    .big_interval {
        background-color: rgba(255, 0, 0, 0.5);
    }
    </style>
    '''
    return html + css
