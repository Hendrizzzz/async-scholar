# Test Fixtures

Fixtures should be synthetic or explicitly authorized.

## Transcript Fixture Format

Use JSONL. Each line is one transcript segment:

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

For detector tests, pair transcript fixtures with expected event files:

```text
tests/fixtures/transcripts/attendance_roll_call.jsonl
tests/fixtures/expected_events/attendance_roll_call.json
```

## Privacy Rule

Do not commit real private class transcripts, recordings, names, meeting links, or auth data.

