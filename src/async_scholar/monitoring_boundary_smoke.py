from __future__ import annotations

from async_scholar.fake_meeting import build_fake_meeting_fixture
from async_scholar.fake_meeting_session import (
    build_fake_meeting_session_history_summary,
    inspect_fake_meeting_session_html,
)

_MONITORING_BOUNDARY_SMOKE_ERROR = "monitoring boundary smoke could not be built"
_EXPECTED_HISTORY_KIND = "synthetic_fake_meeting_session_history"


def build_local_monitoring_boundary_smoke() -> dict[str, object]:
    try:
        fixture = build_fake_meeting_fixture()
        html_text = fixture.to_html_document()
        if type(html_text) is not str or not html_text:
            raise ValueError(_MONITORING_BOUNDARY_SMOKE_ERROR)

        snapshot = inspect_fake_meeting_session_html(html_text)
        history_summary = build_fake_meeting_session_history_summary((snapshot,))
        if (
            type(history_summary) is not dict
            or history_summary.get("history_kind") != _EXPECTED_HISTORY_KIND
            or history_summary.get("snapshot_count") != 1
        ):
            raise ValueError(_MONITORING_BOUNDARY_SMOKE_ERROR)
    except Exception:
        raise RuntimeError(_MONITORING_BOUNDARY_SMOKE_ERROR) from None

    return {
        "smoke_kind": "local_monitoring_boundary",
        "synthetic_fixture_status": "built",
        "html_inspection_status": "inspected",
        "session_history_status": "summarized",
        "monitoring_boundary_evidence_status": "satisfactory",
        "real_online_monitoring_performed": False,
        "browser_automation_performed": False,
        "auth_profile_accessed": False,
        "network_performed": False,
        "audio_capture_performed": False,
        "gate_d_pass_claimed": False,
        "product_promise_alpha_pass_claimed": False,
    }
