"""NiceGUI UI surfaces for AsyncScholar."""

from async_scholar.ui.event_timeline import (
    SAFE_EVENT_TIMELINE_FIELDS,
    EventTimelineEventModel,
    EventTimelineSource,
    EventTimelineView,
    event_to_timeline_model,
    format_event_timeline_event,
    normalize_event_timeline_events,
    render_event_timeline_view,
)
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
    "SAFE_EVENT_TIMELINE_FIELDS",
    "SAFE_STATUS_FIELDS",
    "SAFE_TRANSCRIPT_FIELDS",
    "EventTimelineEventModel",
    "EventTimelineSource",
    "EventTimelineView",
    "SessionStatusModel",
    "SessionStatusView",
    "SessionStatusWorker",
    "TranscriptSegmentModel",
    "TranscriptStreamView",
    "event_to_timeline_model",
    "format_event_timeline_event",
    "format_status_model",
    "format_transcript_segment",
    "normalize_event_timeline_events",
    "normalize_transcript_segments",
    "render_event_timeline_view",
    "render_session_status_view",
    "render_transcript_stream_view",
    "segment_to_transcript_model",
    "snapshot_to_status_model",
]
