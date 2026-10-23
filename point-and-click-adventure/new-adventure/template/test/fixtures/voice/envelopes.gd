# Written by `bun tools/audio/run.ts post` (audio-pipeline.md §4.5); don't edit.
# RATE is values a second. LINES maps each line ID to its loudness envelope:
# base64 bytes, 0 silent to 255 loudest.

const RATE := 30
const LINES := {
	&"TEST_FILE_1": "AAAkUGd6hpKdpKy0ub/Fyc3S1dne4OPn6ezw8fT3+fvfAAAAAAAA",
}
