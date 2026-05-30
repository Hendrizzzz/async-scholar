"""NiceGUI UI surfaces for AsyncScholar."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_LOCAL_ALPHA_DASHBOARD_DEMO_MODULE = "async_scholar.ui.local_alpha_dashboard_demo"

_SYMBOL_MODULES = {
    "ArchiveBrowserItemModel": "async_scholar.ui.archive_browser",
    "ArchiveBrowserSource": "async_scholar.ui.archive_browser",
    "ArchiveBrowserView": "async_scholar.ui.archive_browser",
    "AudioDiagnosticsModel": "async_scholar.ui.audio_diagnostics",
    "AudioDiagnosticsSource": "async_scholar.ui.audio_diagnostics",
    "AudioDiagnosticsView": "async_scholar.ui.audio_diagnostics",
    "GateDStatusModel": "async_scholar.ui.local_alpha_dashboard",
    "LocalAlphaDashboardSources": "async_scholar.ui.local_alpha_dashboard",
    "LocalAlphaDashboardView": "async_scholar.ui.local_alpha_dashboard",
    "LocalAlphaSessionStatusModel": "async_scholar.ui.local_alpha_dashboard",
    "SAFE_ARCHIVE_BROWSER_FIELDS": "async_scholar.ui.archive_browser",
    "SAFE_AUDIO_DIAGNOSTICS_FIELDS": "async_scholar.ui.audio_diagnostics",
    "SAFE_ALERT_HISTORY_FIELDS": "async_scholar.ui.alert_history",
    "SAFE_EVENT_TIMELINE_FIELDS": "async_scholar.ui.event_timeline",
    "SAFE_STATUS_FIELDS": "async_scholar.ui.session_status",
    "SAFE_TRANSCRIPT_FIELDS": "async_scholar.ui.transcript_stream",
    "AlertHistoryAlertModel": "async_scholar.ui.alert_history",
    "AlertHistorySource": "async_scholar.ui.alert_history",
    "AlertHistoryView": "async_scholar.ui.alert_history",
    "EventTimelineEventModel": "async_scholar.ui.event_timeline",
    "EventTimelineSource": "async_scholar.ui.event_timeline",
    "EventTimelineView": "async_scholar.ui.event_timeline",
    "SessionStatusModel": "async_scholar.ui.session_status",
    "SessionStatusView": "async_scholar.ui.session_status",
    "SessionStatusWorker": "async_scholar.ui.session_status",
    "TranscriptSegmentModel": "async_scholar.ui.transcript_stream",
    "TranscriptStreamView": "async_scholar.ui.transcript_stream",
    "archive_item_to_browser_model": "async_scholar.ui.archive_browser",
    "alert_to_history_model": "async_scholar.ui.alert_history",
    "build_local_alpha_dashboard_demo_dry_run": _LOCAL_ALPHA_DASHBOARD_DEMO_MODULE,
    "build_local_alpha_dashboard_demo_sources": _LOCAL_ALPHA_DASHBOARD_DEMO_MODULE,
    "diagnostics_to_audio_model": "async_scholar.ui.audio_diagnostics",
    "event_to_timeline_model": "async_scholar.ui.event_timeline",
    "format_archive_browser_item": "async_scholar.ui.archive_browser",
    "format_alert_history_item": "async_scholar.ui.alert_history",
    "format_gate_d_status": "async_scholar.ui.local_alpha_dashboard",
    "format_audio_diagnostics_model": "async_scholar.ui.audio_diagnostics",
    "format_event_timeline_event": "async_scholar.ui.event_timeline",
    "format_status_model": "async_scholar.ui.session_status",
    "format_transcript_segment": "async_scholar.ui.transcript_stream",
    "normalize_archive_browser_items": "async_scholar.ui.archive_browser",
    "normalize_alert_history_alerts": "async_scholar.ui.alert_history",
    "normalize_audio_diagnostics": "async_scholar.ui.audio_diagnostics",
    "normalize_dashboard_session_status": "async_scholar.ui.local_alpha_dashboard",
    "normalize_event_timeline_events": "async_scholar.ui.event_timeline",
    "normalize_gate_d_status": "async_scholar.ui.local_alpha_dashboard",
    "normalize_transcript_segments": "async_scholar.ui.transcript_stream",
    "render_archive_browser_view": "async_scholar.ui.archive_browser",
    "render_alert_history_view": "async_scholar.ui.alert_history",
    "render_audio_diagnostics_view": "async_scholar.ui.audio_diagnostics",
    "render_event_timeline_view": "async_scholar.ui.event_timeline",
    "render_local_alpha_dashboard_demo_page": _LOCAL_ALPHA_DASHBOARD_DEMO_MODULE,
    "render_local_alpha_dashboard": "async_scholar.ui.local_alpha_dashboard",
    "render_session_status_view": "async_scholar.ui.session_status",
    "render_transcript_stream_view": "async_scholar.ui.transcript_stream",
    "run_local_alpha_dashboard_demo": _LOCAL_ALPHA_DASHBOARD_DEMO_MODULE,
    "segment_to_transcript_model": "async_scholar.ui.transcript_stream",
    "snapshot_to_status_model": "async_scholar.ui.session_status",
}

__all__ = list(_SYMBOL_MODULES)


def __getattr__(name: str) -> Any:
    try:
        module_name = _SYMBOL_MODULES[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    value = getattr(import_module(module_name), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted([*globals(), *__all__])
