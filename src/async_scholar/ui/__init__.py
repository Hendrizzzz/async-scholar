"""NiceGUI UI surfaces for AsyncScholar."""

from async_scholar.ui.session_status import (
    SAFE_STATUS_FIELDS,
    SessionStatusModel,
    SessionStatusView,
    SessionStatusWorker,
    format_status_model,
    render_session_status_view,
    snapshot_to_status_model,
)
from async_scholar.ui.transcript_stream import (
    SAFE_TRANSCRIPT_FIELDS,
    TranscriptSegmentModel,
    TranscriptStreamView,
    format_transcript_segment,
    normalize_transcript_segments,
    render_transcript_stream_view,
    segment_to_transcript_model,
)

__all__ = [
    "SAFE_STATUS_FIELDS",
    "SAFE_TRANSCRIPT_FIELDS",
    "SessionStatusModel",
    "SessionStatusView",
    "SessionStatusWorker",
    "TranscriptSegmentModel",
    "TranscriptStreamView",
    "format_status_model",
    "format_transcript_segment",
    "normalize_transcript_segments",
    "render_session_status_view",
    "render_transcript_stream_view",
    "segment_to_transcript_model",
    "snapshot_to_status_model",
]
