# Test Fixtures

Fixtures should be synthetic or explicitly authorized.

## Transcript Fixture Format

Use JSONL. Each non-empty line is one synthetic transcript segment. The fixture
loader accepts these fields:

- `start_s` maps to `TranscriptSegment.start_seconds`.
- `end_s` maps to `TranscriptSegment.end_seconds`.
- `text` maps to `TranscriptSegment.text`.
- `speaker` maps to `TranscriptSegment.speaker` and may be omitted.

The loader derives deterministic IDs instead of storing them in fixture records:

- `TranscriptSegment.session_id` is `fixture:<fixture-file-stem>`.
- `TranscriptSegment.segment_id` is
  `fixture:<fixture-file-stem>:segment:<one-based-zero-padded-index>`.

```json
{"start_s":0.0,"end_s":3.2,"text":"Good morning class.","speaker":"professor"}
{"start_s":3.2,"end_s":8.0,"text":"For attendance, say present when I call your name.","speaker":"professor"}
```

## Required Fixture Types

- normal lecture
- attendance roll call
- casual name mention
- direct question
- camera/mic request
- pop quiz
- task due in 10 minutes
- deadline change
- dismissal
- noisy transcript
- code-switching transcript

## Expected Events

Expected event files belong to a future event-detector ticket. Do not add them
for transcript-loader fixtures.

```text
tests/fixtures/transcripts/attendance_roll_call.jsonl
tests/fixtures/expected_events/attendance_roll_call.json
```

## Privacy Rule

Do not commit real private class transcripts, recordings, names, meeting links, or auth data.
