.PHONY: run
run:
	python -m uvicorn server:app --host 0.0.0.0 --port 8001 --reload

.PHONY: run_with_midi
run_with_midi:
	MIDI_DEVICE='IAC Driver Bus 1' uvicorn server:app --host 0.0.0.0 --port 8001 --reload
