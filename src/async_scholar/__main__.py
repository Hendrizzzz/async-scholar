from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from async_scholar import __version__
from async_scholar.demo import run_fixture_demo

_CRASH_RECOVERY_PREFLIGHT_CLI_ERROR = (
    "crash recovery session preflight could not be built"
)
_ARCHIVE_EXPORT_PREFLIGHT_CLI_ERROR = "archive export preflight could not be built"
_ARCHIVE_EXPORT_CLI_ERROR = "archive export could not be executed"
_ARCHIVE_EXPORT_VERIFY_CLI_ERROR = "archive export verification could not be built"
_ARCHIVE_DELETE_DRY_RUN_CLI_ERROR = "archive delete dry run could not be built"
_GATE_D_READINESS_CLI_ERROR = "gate d readiness could not be built"
_GATE_D_EVIDENCE_GAP_SUMMARY_CLI_ERROR = (
    "gate d evidence gap summary could not be built"
)
_ALERT_ROUTING_SMOKE_CLI_ERROR = "local alert routing smoke could not be built"
_POLICY_GATE_SMOKE_CLI_ERROR = "policy gate smoke could not be built"
_DELIVERY_PATH_SMOKE_CLI_ERROR = "delivery path smoke could not be built"
_MONITORING_BOUNDARY_SMOKE_CLI_ERROR = "monitoring boundary smoke could not be built"
_GATE_D_SECURITY_REVIEW_EVIDENCE_CLI_ERROR = (
    "gate d security review evidence could not be built"
)
_GATE_D_SECURITY_REVIEW_EVIDENCE_KEYS = (
    "evidence_kind",
    "security_review_status",
    "privacy_boundary_review_status",
    "sanitized_output_review_status",
    "secret_handling_review_status",
    "private_data_boundary_review_status",
    "browser_auth_boundary_review_status",
    "audio_capture_boundary_review_status",
    "scheduler_execution_boundary_review_status",
    "deletion_export_boundary_review_status",
    "browser_automation_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "audio_capture_performed",
    "loopback_capture_performed",
    "network_performed",
    "scheduler_execution_performed",
    "live_delivery_performed",
    "cleanup_or_deletion_performed",
    "export_performed",
    "subprocess_performed",
    "timer_or_sleep_used",
    "dependency_change_performed",
    "public_github_approval_claimed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)
_GATE_D_SECURITY_REVIEW_EVIDENCE_STATUSES = {
    "security_review_status": "satisfactory",
    "privacy_boundary_review_status": "satisfactory",
    "sanitized_output_review_status": "satisfactory",
    "secret_handling_review_status": "satisfactory",
    "private_data_boundary_review_status": "satisfactory",
    "browser_auth_boundary_review_status": "satisfactory",
    "audio_capture_boundary_review_status": "satisfactory",
    "scheduler_execution_boundary_review_status": "satisfactory",
    "deletion_export_boundary_review_status": "satisfactory",
}
_GATE_D_SECURITY_REVIEW_EVIDENCE_FALSE_FLAGS = (
    "browser_automation_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "audio_capture_performed",
    "loopback_capture_performed",
    "network_performed",
    "scheduler_execution_performed",
    "live_delivery_performed",
    "cleanup_or_deletion_performed",
    "export_performed",
    "subprocess_performed",
    "timer_or_sleep_used",
    "dependency_change_performed",
    "public_github_approval_claimed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)
_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_CLI_ERROR = (
    "gate d mic diagnostics after reboot evidence could not be built"
)
_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_KEYS = (
    "evidence_kind",
    "mic_diagnostics_after_reboot_status",
    "recorded_scalar_post_reboot_evidence_status",
    "metadata_only_evidence_status",
    "no_signal_quality_claim_status",
    "no_transcript_usefulness_claim_status",
    "local_only_status",
    "file_io_performed",
    "artifact_read",
    "artifact_created",
    "device_name_exposed",
    "private_path_exposed",
    "transcript_text_exposed",
    "audio_capture_performed",
    "recording_performed",
    "vad_performed",
    "stt_performed",
    "signal_quality_claimed",
    "transcript_usefulness_claimed",
    "network_performed",
    "browser_automation_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "scheduler_execution_performed",
    "live_delivery_performed",
    "cleanup_or_deletion_performed",
    "export_performed",
    "dependency_change_performed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)
_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_STATUSES = {
    "mic_diagnostics_after_reboot_status": "satisfactory",
    "recorded_scalar_post_reboot_evidence_status": "satisfactory",
    "metadata_only_evidence_status": "documented",
    "no_signal_quality_claim_status": "documented",
    "no_transcript_usefulness_claim_status": "documented",
    "local_only_status": "documented",
}
_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_FALSE_FLAGS = (
    "file_io_performed",
    "artifact_read",
    "artifact_created",
    "device_name_exposed",
    "private_path_exposed",
    "transcript_text_exposed",
    "audio_capture_performed",
    "recording_performed",
    "vad_performed",
    "stt_performed",
    "signal_quality_claimed",
    "transcript_usefulness_claimed",
    "network_performed",
    "browser_automation_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "scheduler_execution_performed",
    "live_delivery_performed",
    "cleanup_or_deletion_performed",
    "export_performed",
    "dependency_change_performed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)
_GATE_D_SIGNAL_QUALITY_EVIDENCE_CLI_ERROR = (
    "gate d signal quality evidence could not be built"
)
_GATE_D_SIGNAL_QUALITY_EVIDENCE_KEYS = (
    "evidence_kind",
    "signal_quality_evidence_status",
    "ticket_126_public_open_evidence_status",
    "metadata_only_evidence_status",
    "public_open_evidence_status",
    "public_open_sample_rate_hz",
    "public_open_duration_seconds",
    "public_open_vad_segment_count",
    "public_open_stt_segment_count",
    "public_open_elapsed_seconds",
    "public_open_real_time_factor",
    "artifact_presence_checks_passed",
    "no_local_microphone_quality_claim_status",
    "no_transcript_usefulness_claim_status",
    "no_real_online_monitoring_claim_status",
    "no_live_delivery_claim_status",
    "file_io_performed",
    "artifact_read",
    "artifact_created",
    "download_performed",
    "audio_capture_performed",
    "recording_performed",
    "vad_execution_performed",
    "stt_execution_performed",
    "model_loaded",
    "subprocess_performed",
    "network_performed",
    "browser_automation_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "hardware_or_device_enumeration_performed",
    "scheduler_execution_performed",
    "live_delivery_performed",
    "cleanup_or_deletion_performed",
    "export_performed",
    "dependency_change_performed",
    "local_microphone_quality_claimed",
    "transcript_usefulness_claimed",
    "real_online_monitoring_claimed",
    "live_alert_delivery_claimed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)
_GATE_D_SIGNAL_QUALITY_EVIDENCE_STATUSES = {
    "signal_quality_evidence_status": "satisfactory",
    "ticket_126_public_open_evidence_status": "documented",
    "metadata_only_evidence_status": "documented",
    "public_open_evidence_status": "documented",
    "no_local_microphone_quality_claim_status": "documented",
    "no_transcript_usefulness_claim_status": "documented",
    "no_real_online_monitoring_claim_status": "documented",
    "no_live_delivery_claim_status": "documented",
}
_GATE_D_SIGNAL_QUALITY_EVIDENCE_SCALARS = {
    "public_open_sample_rate_hz": 16000,
    "public_open_duration_seconds": 68.370375,
    "public_open_vad_segment_count": 32,
    "public_open_stt_segment_count": 16,
    "public_open_elapsed_seconds": 4.515231,
    "public_open_real_time_factor": 0.066041,
}
_GATE_D_SIGNAL_QUALITY_EVIDENCE_TRUE_FLAGS = ("artifact_presence_checks_passed",)
_GATE_D_SIGNAL_QUALITY_EVIDENCE_FALSE_FLAGS = (
    "file_io_performed",
    "artifact_read",
    "artifact_created",
    "download_performed",
    "audio_capture_performed",
    "recording_performed",
    "vad_execution_performed",
    "stt_execution_performed",
    "model_loaded",
    "subprocess_performed",
    "network_performed",
    "browser_automation_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "hardware_or_device_enumeration_performed",
    "scheduler_execution_performed",
    "live_delivery_performed",
    "cleanup_or_deletion_performed",
    "export_performed",
    "dependency_change_performed",
    "local_microphone_quality_claimed",
    "transcript_usefulness_claimed",
    "real_online_monitoring_claimed",
    "live_alert_delivery_claimed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)
_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_CLI_ERROR = (
    "gate d product judgment evidence could not be built"
)
_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_KEYS = (
    "evidence_kind",
    "product_judgment_evidence_status",
    "manual_product_judgment_required_status",
    "manual_product_judgment_recorded",
    "metadata_only_evidence_status",
    "no_gate_d_pass_claim_status",
    "no_product_promise_alpha_pass_claim_status",
    "no_real_online_monitoring_claim_status",
    "no_live_delivery_claim_status",
    "no_transcript_usefulness_claim_status",
    "no_local_microphone_quality_claim_status",
    "file_io_performed",
    "artifact_read",
    "artifact_created",
    "download_performed",
    "audio_capture_performed",
    "recording_performed",
    "vad_execution_performed",
    "stt_execution_performed",
    "model_loaded",
    "subprocess_performed",
    "network_performed",
    "browser_automation_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "scheduler_execution_performed",
    "live_delivery_performed",
    "cleanup_or_deletion_performed",
    "export_performed",
    "dependency_change_performed",
    "real_online_monitoring_claimed",
    "live_alert_delivery_claimed",
    "transcript_usefulness_claimed",
    "local_microphone_quality_claimed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)
_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_STATUSES = {
    "product_judgment_evidence_status": "blocking",
    "manual_product_judgment_required_status": "required",
    "metadata_only_evidence_status": "documented",
    "no_gate_d_pass_claim_status": "documented",
    "no_product_promise_alpha_pass_claim_status": "documented",
    "no_real_online_monitoring_claim_status": "documented",
    "no_live_delivery_claim_status": "documented",
    "no_transcript_usefulness_claim_status": "documented",
    "no_local_microphone_quality_claim_status": "documented",
}
_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_FALSE_FLAGS = (
    "manual_product_judgment_recorded",
    "file_io_performed",
    "artifact_read",
    "artifact_created",
    "download_performed",
    "audio_capture_performed",
    "recording_performed",
    "vad_execution_performed",
    "stt_execution_performed",
    "model_loaded",
    "subprocess_performed",
    "network_performed",
    "browser_automation_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "scheduler_execution_performed",
    "live_delivery_performed",
    "cleanup_or_deletion_performed",
    "export_performed",
    "dependency_change_performed",
    "real_online_monitoring_claimed",
    "live_alert_delivery_claimed",
    "transcript_usefulness_claimed",
    "local_microphone_quality_claimed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)
_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_CLI_ERROR = (
    "gate d scheduler lifecycle evidence could not be built"
)
_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_KEYS = (
    "evidence_kind",
    "scheduler_lifecycle_evidence_status",
    "explicit_invocation_boundary_status",
    "metadata_only_lifecycle_status",
    "no_background_loop_status",
    "no_timer_status",
    "no_scheduler_runtime_import_status",
    "local_only_status",
    "file_io_performed",
    "sqlite_accessed",
    "scheduler_execution_performed",
    "scheduler_runtime_imported",
    "scheduler_lifecycle_smoke_performed",
    "background_loop_performed",
    "timer_or_sleep_used",
    "daemon_or_recurring_job_performed",
    "subprocess_performed",
    "network_performed",
    "browser_automation_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "audio_capture_performed",
    "loopback_capture_performed",
    "live_delivery_performed",
    "cleanup_or_deletion_performed",
    "export_performed",
    "dependency_change_performed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)
_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_STATUSES = {
    "scheduler_lifecycle_evidence_status": "satisfactory",
    "explicit_invocation_boundary_status": "documented",
    "metadata_only_lifecycle_status": "documented",
    "no_background_loop_status": "documented",
    "no_timer_status": "documented",
    "no_scheduler_runtime_import_status": "documented",
    "local_only_status": "documented",
}
_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_FALSE_FLAGS = (
    "file_io_performed",
    "sqlite_accessed",
    "scheduler_execution_performed",
    "scheduler_runtime_imported",
    "scheduler_lifecycle_smoke_performed",
    "background_loop_performed",
    "timer_or_sleep_used",
    "daemon_or_recurring_job_performed",
    "subprocess_performed",
    "network_performed",
    "browser_automation_performed",
    "auth_profile_accessed",
    "cookie_accessed",
    "private_data_read",
    "audio_capture_performed",
    "loopback_capture_performed",
    "live_delivery_performed",
    "cleanup_or_deletion_performed",
    "export_performed",
    "dependency_change_performed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
    "autonomous_participation_performed",
    "academic_answer_behavior_performed",
)
_GATE_D_ROLLBACK_PLAN_EVIDENCE_CLI_ERROR = (
    "gate d rollback plan evidence could not be built"
)
_GATE_D_ROLLBACK_PLAN_EVIDENCE_KEYS = (
    "evidence_kind",
    "rollback_plan_for_loopback_playwright_spike_status",
    "rollback_plan_document_status",
    "rollback_trigger_coverage_status",
    "disable_strategy_status",
    "dependency_rollback_status",
    "disposable_browser_state_cleanup_status",
    "artifact_cleanup_status",
    "private_data_handling_status",
    "manual_checks_status",
    "stop_conditions_status",
    "browser_automation_performed",
    "audio_capture_performed",
    "loopback_capture_performed",
    "network_performed",
    "live_delivery_performed",
    "filesystem_cleanup_performed",
    "dependency_change_performed",
    "external_platform_accessed",
    "profile_state_accessed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
)
_GATE_D_ROLLBACK_PLAN_EVIDENCE_STATUSES = {
    "rollback_plan_for_loopback_playwright_spike_status": "satisfactory",
    "rollback_plan_document_status": "tracked",
    "rollback_trigger_coverage_status": "documented",
    "disable_strategy_status": "documented",
    "dependency_rollback_status": "documented",
    "disposable_browser_state_cleanup_status": "documented",
    "artifact_cleanup_status": "documented",
    "private_data_handling_status": "documented",
    "manual_checks_status": "documented",
    "stop_conditions_status": "documented",
}
_GATE_D_ROLLBACK_PLAN_EVIDENCE_FALSE_FLAGS = (
    "browser_automation_performed",
    "audio_capture_performed",
    "loopback_capture_performed",
    "network_performed",
    "live_delivery_performed",
    "filesystem_cleanup_performed",
    "dependency_change_performed",
    "external_platform_accessed",
    "profile_state_accessed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
)
_GATE_D_LOCAL_EVIDENCE_BUNDLE_CLI_ERROR = (
    "gate d local evidence bundle could not be built"
)
_GATE_D_LOCAL_EVIDENCE_BUNDLE_KEYS = (
    "bundle_kind",
    "mic_diagnostics_after_reboot_status",
    "alert_routing_status",
    "security_review_status",
    "policy_gate_tests_status",
    "rollback_plan_for_loopback_playwright_spike_status",
    "signal_quality_evidence_status",
    "scheduler_lifecycle_evidence_status",
    "delivery_path_evidence_status",
    "monitoring_boundary_evidence_status",
    "product_judgment_evidence_status",
    "missing_evidence",
    "missing_evidence_count",
    "blocking_evidence",
    "blocking_evidence_count",
    "satisfactory_evidence_count",
    "ready_for_gate_review",
    "readiness_decision",
    "readiness_reason",
    "gap_decision",
    "gap_reason",
    "live_delivery_performed",
    "real_online_monitoring_performed",
    "browser_automation_performed",
    "audio_capture_performed",
    "scheduler_execution_performed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
)
_GATE_D_LOCAL_EVIDENCE_BUNDLE_STATUSES = {
    "mic_diagnostics_after_reboot_status": "satisfactory",
    "alert_routing_status": "satisfactory",
    "security_review_status": "satisfactory",
    "policy_gate_tests_status": "satisfactory",
    "rollback_plan_for_loopback_playwright_spike_status": "satisfactory",
    "signal_quality_evidence_status": "satisfactory",
    "scheduler_lifecycle_evidence_status": "satisfactory",
    "delivery_path_evidence_status": "satisfactory",
    "monitoring_boundary_evidence_status": "satisfactory",
    "product_judgment_evidence_status": "blocking",
}
_GATE_D_LOCAL_EVIDENCE_BUNDLE_MISSING: list[str] = []
_GATE_D_LOCAL_EVIDENCE_BUNDLE_BLOCKING = [
    "product_judgment_evidence",
]
_GATE_D_LOCAL_EVIDENCE_BUNDLE_FALSE_FLAGS = (
    "ready_for_gate_review",
    "live_delivery_performed",
    "real_online_monitoring_performed",
    "browser_automation_performed",
    "audio_capture_performed",
    "scheduler_execution_performed",
    "gate_d_pass_claimed",
    "product_promise_alpha_pass_claimed",
)
_SESSION_WINDOW_LIFECYCLE_SMOKE_CLI_ERROR = (
    "session window lifecycle smoke could not be built"
)
_SCHEDULED_START_PREVIEW_CLI_ERROR = "scheduled start preview could not be built"
_COURSE_SCHEDULE_SAVE_CLI_ERROR = "course schedule save could not be built"
_COURSE_SCHEDULE_SUMMARY_CLI_ERROR = "course schedule summary could not be built"
_COURSE_SCHEDULE_LIST_CLI_ERROR = "course schedule list could not be built"
_SCHEDULED_START_PREVIEW_FROM_STORE_CLI_ERROR = (
    "stored scheduled start preview could not be built"
)
_SCHEDULED_START_NEXT_FROM_STORE_CLI_ERROR = (
    "stored next scheduled start preview could not be built"
)
_SCHEDULED_START_DUE_LIST_FROM_STORE_CLI_ERROR = (
    "stored scheduled start due list could not be built"
)
_SESSION_STOP_PREVIEW_FROM_STORE_CLI_ERROR = (
    "stored session stop preview could not be built"
)
_SESSION_WINDOW_PLAN_FROM_STORE_CLI_ERROR = (
    "stored session window plan could not be built"
)
_SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR = (
    "stored session window archive preflight could not be built"
)
_SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR = (
    "stored session window alert preview could not be built"
)
_SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR = (
    "stored session window readiness preflight could not be built"
)
_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR = (
    "stored session window confirmation preflight could not be built"
)
_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR = (
    "stored session window confirmation response could not be built"
)
_SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR = (
    "stored session window start authorization could not be built"
)
_SESSION_WINDOW_EXECUTION_PREFLIGHT_FROM_STORE_CLI_ERROR = (
    "stored session window execution preflight could not be built"
)
_SESSION_WINDOW_EXECUTION_FROM_STORE_CLI_ERROR = (
    "stored session window execution could not be built"
)
_SESSION_WINDOW_START_RECEIPT_FROM_STORE_CLI_ERROR = (
    "stored session window start receipt could not be built"
)
_SESSION_WINDOW_STOP_EXECUTION_PREFLIGHT_FROM_STORE_CLI_ERROR = (
    "stored session window stop execution preflight could not be built"
)
_SESSION_WINDOW_STOP_EXECUTION_FROM_STORE_CLI_ERROR = (
    "stored session window stop execution could not be built"
)
_SESSION_WINDOW_STOP_RECEIPT_FROM_STORE_CLI_ERROR = (
    "stored session window stop receipt could not be built"
)
_SESSION_WINDOW_RUNTIME_SUMMARY_CLI_ERROR = (
    "stored session window runtime summary could not be built"
)
_SESSION_WINDOW_RECOVERY_DECISION_CLI_ERROR = (
    "stored session window recovery decision could not be built"
)
_SESSION_WINDOW_RECOVERY_REVIEW_CLI_ERROR = (
    "stored session window recovery review could not be built"
)
_SESSION_WINDOW_RECOVERY_REVIEW_BATCH_CLI_ERROR = (
    "stored session window recovery review batch could not be built"
)
_SESSION_WINDOW_RECOVERY_REPORT_CLI_ERROR = (
    "stored session window recovery report could not be built"
)
_SESSION_WINDOW_RECOVERY_REPORT_FILE_CLI_ERROR = (
    "stored session window recovery report file could not be written"
)
_SESSION_WINDOW_RECOVERY_REPORT_FILE_INVENTORY_CLI_ERROR = (
    "stored session window recovery report file inventory could not be built"
)
_SESSION_WINDOW_RECOVERY_REPORT_FILE_VERIFICATION_CLI_ERROR = (
    "stored session window recovery report file verification could not be built"
)
_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_PREVIEW_CLI_ERROR = (
    "stored session window recovery report file action preview could not be built"
)
_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_CLI_ERROR = (
    "stored session window recovery report file action could not be applied"
)
_SESSION_WINDOW_RECOVERY_REPORT_FILE_STATUS_CLI_ERROR = (
    "stored session window recovery report file status could not be built"
)
_GATE_D_READINESS_STATUSES = ("satisfactory", "blocking", "missing")
_COURSE_SCHEDULE_SAFE_SUMMARY_KEYS = ("course_id", "class_time_count")
_STORED_SCHEDULED_START_PREVIEW_KEYS = (
    "status",
    "session_id",
    "course_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "next_day_of_week",
    "next_local_start_time",
)
_STORED_SCHEDULED_START_NEXT_PREVIEW_KEYS = (
    "status",
    "session_id",
    "course_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "next_day_of_week",
    "next_local_start_time",
)
_STORED_SCHEDULED_START_DUE_LIST_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "courses",
)
_STORED_SCHEDULED_START_DUE_LIST_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
)
_STORED_SESSION_STOP_PREVIEW_KEYS = (
    "status",
    "course_id",
    "source_kind",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "stop_after_minutes",
    "enabled",
)
_STORED_SESSION_WINDOW_PLAN_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "courses",
)
_STORED_SESSION_WINDOW_PLAN_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
)
_STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "archive_recovery_status",
    "archive_existing_count",
    "archive_missing_count",
    "archive_total_existing_size_bytes",
    "courses",
)
_STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
)
_STORED_SESSION_WINDOW_ALERT_PREVIEW_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "alert_preview_count",
    "courses",
)
_STORED_SESSION_WINDOW_ALERT_PREVIEW_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "alert_preview",
)
_STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA_KEYS = (
    "alert_kind",
    "delivery",
    "requires_confirmation",
)
_STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA = {
    "alert_kind": "participation_check",
    "delivery": "none",
    "requires_confirmation": True,
}
_STORED_SESSION_WINDOW_READINESS_PREFLIGHT_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "alert_preview_count",
    "archive_recovery_status",
    "archive_existing_count",
    "archive_missing_count",
    "archive_total_existing_size_bytes",
    "ready_to_start",
    "courses",
)
_STORED_SESSION_WINDOW_READINESS_PREFLIGHT_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "alert_preview",
)
_STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "ready_to_start",
    "confirmation_required",
    "confirmation_status",
    "blocked_execution_count",
    "courses",
)
_STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "requires_confirmation",
)
_STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_STATUSES = frozenset(
    ("not_required", "required", "disabled")
)
_STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "ready_to_start",
    "confirmation_required",
    "confirmation_status",
    "confirmation_response",
    "confirmation_verified",
    "confirmed_start_count",
    "blocked_execution_count",
    "courses",
)
_STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "requires_confirmation",
    "confirmation_response",
)
_STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_STATUSES = frozenset(
    ("confirmed", "declined", "not_required", "disabled")
)
_STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_TOKENS = frozenset(
    ("confirmed", "declined")
)
_STORED_SESSION_WINDOW_START_AUTHORIZATION_KEYS = (
    "status",
    "session_id",
    "source_kind",
    "clock_day_of_week",
    "clock_local_time",
    "course_count",
    "due_count",
    "ready_to_start",
    "confirmation_required",
    "confirmation_status",
    "confirmation_response",
    "confirmation_verified",
    "authorized",
    "authorized_start_count",
    "blocked_start_count",
    "block_reason",
    "courses",
)
_STORED_SESSION_WINDOW_START_AUTHORIZATION_COURSE_KEYS = (
    "course_id",
    "selected_class_time_index",
    "scheduled_day_of_week",
    "scheduled_local_start_time",
    "due",
    "minutes_until_start",
    "stop_after_minutes",
    "enabled",
    "requires_confirmation",
    "confirmation_response",
    "authorized",
)
_STORED_SESSION_WINDOW_START_AUTHORIZATION_STATUSES = frozenset(
    ("authorized", "blocked", "not_authorized", "not_required", "disabled")
)
_STORED_SESSION_WINDOW_START_AUTHORIZATION_BLOCK_REASONS = frozenset(
    (
        "none",
        "confirmation_declined",
        "confirmation_not_verified",
        "disabled",
        "not_ready",
        "not_ready_to_start",
        "not_required",
        "confirmation_not_required",
        "no_due_courses",
    )
)


class _FixedMessageArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args: object, fixed_error_message: str, **kwargs: object):
        super().__init__(*args, **kwargs)
        self._fixed_error_message = fixed_error_message

    def error(self, message: str) -> None:
        self.exit(2, f"{self._fixed_error_message}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="async_scholar",
        description=(
            "AsyncScholar is a local-first lecture monitoring scaffold for "
            "transcription, event detection, alerts, archives, and review."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command")
    fixture_demo = subparsers.add_parser(
        "fixture-demo",
        help="run a transcript fixture through event detection and file artifacts",
    )
    fixture_demo.add_argument(
        "fixture_path",
        type=Path,
        help="path to a transcript JSONL fixture",
    )
    fixture_demo.add_argument(
        "--output-root",
        type=Path,
        default=Path("data") / "sessions",
        help="root directory for generated session artifacts",
    )
    fixture_demo.set_defaults(handler=_run_fixture_demo_command)

    recovery_preflight = subparsers.add_parser(
        "crash-recovery-preflight",
        help="summarize read-only crash-recovery metadata for a session",
        description=(
            "Summarize read-only crash-recovery metadata for one explicit session root."
        ),
    )
    _add_crash_recovery_preflight_arguments(recovery_preflight)
    recovery_preflight.set_defaults(handler=_run_crash_recovery_preflight_command)

    archive_export_preflight = subparsers.add_parser(
        "archive-export-preflight",
        help="summarize read-only archive export metadata for a session",
        description=(
            "Summarize read-only archive export metadata for one explicit "
            "session archive root."
        ),
    )
    _add_archive_export_preflight_arguments(archive_export_preflight)
    archive_export_preflight.set_defaults(handler=_run_archive_export_preflight_command)

    archive_export_local = subparsers.add_parser(
        "archive-export-local",
        help="copy allowlisted archive artifacts to an explicit local export root",
        description=(
            "Copy allowlisted archive artifacts for one explicit local session "
            "archive root to one explicit existing local export root."
        ),
    )
    _add_archive_export_local_arguments(archive_export_local)
    archive_export_local.set_defaults(handler=_run_archive_export_local_command)

    archive_export_verify = subparsers.add_parser(
        "archive-export-verify-local",
        help="verify a local archive export using metadata only",
        description=(
            "Verify allowlisted archive export metadata for one explicit local "
            "session archive root and one explicit existing local export root."
        ),
    )
    _add_archive_export_verify_local_arguments(archive_export_verify)
    archive_export_verify.set_defaults(handler=_run_archive_export_verify_local_command)

    archive_delete_dry_run = subparsers.add_parser(
        "archive-delete-dry-run-local",
        help="summarize a local archive delete dry run using metadata only",
        description=(
            "Summarize a read-only local archive delete dry run for one "
            "explicit session archive root."
        ),
    )
    _add_archive_delete_dry_run_local_arguments(archive_delete_dry_run)
    archive_delete_dry_run.set_defaults(
        handler=_run_archive_delete_dry_run_local_command
    )

    gate_d_readiness = subparsers.add_parser(
        "gate-d-readiness-local",
        help="summarize Gate D readiness metadata without executing anything",
        description=(
            "Build a metadata-only Gate D readiness report from explicit scalar "
            "evidence status flags."
        ),
    )
    _add_gate_d_readiness_local_arguments(gate_d_readiness)
    gate_d_readiness.set_defaults(handler=_run_gate_d_readiness_local_command)

    gate_d_evidence_gaps = subparsers.add_parser(
        "gate-d-evidence-gaps-local",
        help="summarize Gate D evidence gaps without executing anything",
        description=(
            "Build a metadata-only Gate D evidence gap summary from explicit "
            "scalar evidence status flags."
        ),
    )
    _add_gate_d_readiness_local_arguments(gate_d_evidence_gaps)
    gate_d_evidence_gaps.set_defaults(handler=_run_gate_d_evidence_gaps_local_command)

    alert_routing_smoke = subparsers.add_parser(
        "alert-routing-smoke-local",
        help="run a local in-process alert routing smoke",
        description=(
            "Route one controlled local alert through the existing in-process "
            "dispatch boundary."
        ),
    )
    _add_alert_routing_smoke_local_arguments(alert_routing_smoke)
    alert_routing_smoke.set_defaults(handler=_run_alert_routing_smoke_local_command)

    policy_gate_smoke = subparsers.add_parser(
        "policy-gate-smoke-local",
        help="summarize local policy-gate smoke evidence",
        description=(
            "Build a metadata-only local policy-gate smoke summary from fixed "
            "synthetic checks."
        ),
    )
    policy_gate_smoke.set_defaults(handler=_run_policy_gate_smoke_local_command)

    delivery_path_smoke = subparsers.add_parser(
        "delivery-path-smoke-local",
        help="summarize local delivery-path smoke evidence",
        description=(
            "Build a metadata-only local delivery-path smoke summary from fixed "
            "synthetic checks."
        ),
    )
    delivery_path_smoke.set_defaults(handler=_run_delivery_path_smoke_local_command)

    monitoring_boundary_smoke = subparsers.add_parser(
        "monitoring-boundary-smoke-local",
        help="summarize local monitoring-boundary smoke evidence",
        description=(
            "Build a metadata-only local monitoring-boundary smoke summary "
            "from fixed synthetic checks."
        ),
    )
    monitoring_boundary_smoke.set_defaults(
        handler=_run_monitoring_boundary_smoke_local_command
    )

    gate_d_security_review_evidence = subparsers.add_parser(
        "gate-d-security-review-evidence-local",
        help="summarize local Gate D security-review evidence",
        description=(
            "Build a metadata-only local Gate D security-review evidence summary "
            "from fixed checks."
        ),
    )
    gate_d_security_review_evidence.set_defaults(
        handler=_run_gate_d_security_review_evidence_local_command
    )

    gate_d_mic_diagnostics_after_reboot_evidence = subparsers.add_parser(
        "gate-d-mic-diagnostics-after-reboot-evidence-local",
        help="summarize local Gate D mic diagnostics after-reboot evidence",
        description=(
            "Build a metadata-only local Gate D mic diagnostics after-reboot "
            "evidence summary from fixed checks."
        ),
    )
    gate_d_mic_diagnostics_after_reboot_evidence.set_defaults(
        handler=_run_gate_d_mic_diagnostics_after_reboot_evidence_local_command
    )

    gate_d_signal_quality_evidence = subparsers.add_parser(
        "gate-d-signal-quality-evidence-local",
        help="summarize local Gate D public-open signal quality evidence",
        description=(
            "Build a metadata-only local Gate D public-open signal quality "
            "evidence summary from fixed checks."
        ),
    )
    gate_d_signal_quality_evidence.set_defaults(
        handler=_run_gate_d_signal_quality_evidence_local_command
    )

    gate_d_product_judgment_evidence = subparsers.add_parser(
        "gate-d-product-judgment-evidence-local",
        help="summarize local Gate D product-judgment evidence",
        description=(
            "Build a metadata-only local Gate D product-judgment evidence "
            "summary from fixed checks."
        ),
    )
    gate_d_product_judgment_evidence.set_defaults(
        handler=_run_gate_d_product_judgment_evidence_local_command
    )

    gate_d_scheduler_lifecycle_evidence = subparsers.add_parser(
        "gate-d-scheduler-lifecycle-evidence-local",
        help="summarize local Gate D scheduler-lifecycle evidence",
        description=(
            "Build a metadata-only local Gate D scheduler-lifecycle evidence "
            "summary from fixed checks."
        ),
    )
    gate_d_scheduler_lifecycle_evidence.set_defaults(
        handler=_run_gate_d_scheduler_lifecycle_evidence_local_command
    )

    gate_d_rollback_plan_evidence = subparsers.add_parser(
        "gate-d-rollback-plan-evidence-local",
        help="summarize local Gate D rollback-plan evidence",
        description=(
            "Build a metadata-only local Gate D rollback-plan evidence summary "
            "from fixed checks."
        ),
    )
    gate_d_rollback_plan_evidence.set_defaults(
        handler=_run_gate_d_rollback_plan_evidence_local_command
    )

    gate_d_local_evidence_bundle = subparsers.add_parser(
        "gate-d-local-evidence-bundle",
        help="summarize local Gate D smoke evidence",
        description=(
            "Build a metadata-only local Gate D smoke evidence bundle from "
            "fixed synthetic checks."
        ),
    )
    gate_d_local_evidence_bundle.set_defaults(
        handler=_run_gate_d_local_evidence_bundle_command
    )

    session_window_lifecycle_smoke = subparsers.add_parser(
        "session-window-lifecycle-smoke-local",
        help="run a local session-window lifecycle smoke",
        description=(
            "Run one bounded local session-window start and stop lifecycle with "
            "fixed synthetic metadata."
        ),
    )
    _add_session_window_lifecycle_smoke_local_arguments(session_window_lifecycle_smoke)
    session_window_lifecycle_smoke.set_defaults(
        handler=_run_session_window_lifecycle_smoke_local_command
    )

    scheduled_start_preview = subparsers.add_parser(
        "scheduled-start-preview-local",
        help="preview scheduled-start metadata without executing",
        description=(
            "Preview one non-executing scheduled-start decision from explicit "
            "local metadata and an explicit local clock."
        ),
    )
    _add_scheduled_start_preview_local_arguments(scheduled_start_preview)
    scheduled_start_preview.set_defaults(
        handler=_run_scheduled_start_preview_local_command
    )

    course_schedule_summary = subparsers.add_parser(
        "course-schedule-summary-local",
        help="summarize a stored local course schedule using metadata only",
        description=(
            "Summarize one stored local course schedule from an explicit "
            "read-only SQLite database path."
        ),
    )
    _add_course_schedule_summary_local_arguments(course_schedule_summary)
    course_schedule_summary.set_defaults(
        handler=_run_course_schedule_summary_local_command
    )

    course_schedule_list = subparsers.add_parser(
        "course-schedule-list-local",
        help="list stored local course schedules using metadata only",
        description=(
            "List stored local course schedule metadata from an explicit "
            "read-only SQLite database path."
        ),
    )
    _add_course_schedule_list_local_arguments(course_schedule_list)
    course_schedule_list.set_defaults(handler=_run_course_schedule_list_local_command)

    course_schedule_save = subparsers.add_parser(
        "course-schedule-save-local",
        help="save a local course schedule from explicit metadata",
        description=(
            "Save one validated local course schedule into an explicit SQLite "
            "database path without executing a scheduler."
        ),
    )
    _add_course_schedule_save_local_arguments(course_schedule_save)
    course_schedule_save.set_defaults(handler=_run_course_schedule_save_local_command)

    stored_schedule_preview = subparsers.add_parser(
        "scheduled-start-preview-from-store-local",
        help="preview stored scheduled-start metadata without executing",
        description=(
            "Preview one non-executing scheduled-start decision from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
    )
    _add_scheduled_start_preview_from_store_local_arguments(stored_schedule_preview)
    stored_schedule_preview.set_defaults(
        handler=_run_scheduled_start_preview_from_store_local_command
    )

    stored_schedule_next_preview = subparsers.add_parser(
        "scheduled-start-next-from-store-local",
        help="preview the next stored scheduled-start metadata without executing",
        description=(
            "Preview the next non-executing scheduled-start decision from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
    )
    _add_scheduled_start_next_from_store_local_arguments(stored_schedule_next_preview)
    stored_schedule_next_preview.set_defaults(
        handler=_run_scheduled_start_next_from_store_local_command
    )

    stored_schedule_due_list = subparsers.add_parser(
        "scheduled-start-due-list-from-store-local",
        help="list due stored scheduled-start metadata without executing",
        description=(
            "List due non-executing scheduled-start metadata from an explicit "
            "read-only local schedule store and explicit local clock."
        ),
    )
    _add_scheduled_start_due_list_from_store_local_arguments(stored_schedule_due_list)
    stored_schedule_due_list.set_defaults(
        handler=_run_scheduled_start_due_list_from_store_local_command
    )

    session_stop_preview = subparsers.add_parser(
        "session-stop-preview-from-store-local",
        help="preview stored session-stop metadata without executing",
        description=(
            "Preview one non-executing session-stop decision from an explicit "
            "read-only local schedule store."
        ),
    )
    _add_session_stop_preview_from_store_local_arguments(session_stop_preview)
    session_stop_preview.set_defaults(
        handler=_run_session_stop_preview_from_store_local_command
    )

    session_window_plan = subparsers.add_parser(
        "session-window-plan-from-store-local",
        help="plan due stored session windows without executing",
        description=(
            "Build due non-executing session-window metadata from an explicit "
            "read-only local schedule store and explicit local clock."
        ),
    )
    _add_session_window_plan_from_store_local_arguments(session_window_plan)
    session_window_plan.set_defaults(
        handler=_run_session_window_plan_from_store_local_command
    )

    session_window_archive_preflight = subparsers.add_parser(
        "session-window-archive-preflight-from-store-local",
        help="preflight due stored session windows against archive readiness",
        description=(
            "Build read-only session-window archive preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
    )
    _add_session_window_archive_preflight_from_store_local_arguments(
        session_window_archive_preflight
    )
    session_window_archive_preflight.set_defaults(
        handler=_run_session_window_archive_preflight_from_store_local_command
    )

    session_window_alert_preview = subparsers.add_parser(
        "session-window-alert-preview-from-store-local",
        help="preview due stored session-window participation checks without delivery",
        description=(
            "Build metadata-only session-window alert preview data from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
    )
    _add_session_window_alert_preview_from_store_local_arguments(
        session_window_alert_preview
    )
    session_window_alert_preview.set_defaults(
        handler=_run_session_window_alert_preview_from_store_local_command
    )

    session_window_readiness_preflight = subparsers.add_parser(
        "session-window-readiness-preflight-from-store-local",
        help="preflight due stored session windows for metadata-only readiness",
        description=(
            "Build read-only session-window readiness preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
    )
    _add_session_window_readiness_preflight_from_store_local_arguments(
        session_window_readiness_preflight
    )
    session_window_readiness_preflight.set_defaults(
        handler=_run_session_window_readiness_preflight_from_store_local_command
    )

    session_window_confirmation_preflight = subparsers.add_parser(
        "session-window-confirmation-preflight-from-store-local",
        help="preflight due stored session windows for user confirmation",
        description=(
            "Build read-only session-window confirmation preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
    )
    _add_session_window_confirmation_preflight_from_store_local_arguments(
        session_window_confirmation_preflight
    )
    session_window_confirmation_preflight.set_defaults(
        handler=_run_session_window_confirmation_preflight_from_store_local_command
    )

    session_window_confirmation_response = subparsers.add_parser(
        "session-window-confirmation-response-from-store-local",
        help="record a fixed user confirmation response for due stored session windows",
        description=(
            "Build non-executing session-window confirmation response metadata from "
            "an explicit read-only local schedule store, archive root, local clock, "
            "and fixed confirmation response."
        ),
    )
    _add_session_window_confirmation_response_from_store_local_arguments(
        session_window_confirmation_response
    )
    session_window_confirmation_response.set_defaults(
        handler=_run_session_window_confirmation_response_from_store_local_command
    )

    session_window_start_authorization = subparsers.add_parser(
        "session-window-start-authorization-from-store-local",
        help="authorize due stored session-window starts after fixed confirmation",
        description=(
            "Build non-executing session-window start authorization metadata from "
            "an explicit read-only local schedule store, archive root, local clock, "
            "and fixed confirmation response."
        ),
    )
    _add_session_window_start_authorization_from_store_local_arguments(
        session_window_start_authorization
    )
    session_window_start_authorization.set_defaults(
        handler=_run_session_window_start_authorization_from_store_local_command
    )

    session_window_execution_preflight = subparsers.add_parser(
        "session-window-execution-preflight-from-store-local",
        help="preflight a one-shot stored session-window execution without running it",
        description=(
            "Build read-only one-shot session-window execution preflight metadata "
            "from an explicit read-only local schedule store, archive root, local "
            "clock, and same-invocation fixed confirmation response."
        ),
    )
    _add_session_window_execution_preflight_from_store_local_arguments(
        session_window_execution_preflight
    )
    session_window_execution_preflight.set_defaults(
        handler=_run_session_window_execution_preflight_from_store_local_command
    )

    session_window_execution = subparsers.add_parser(
        "session-window-execute-from-store-local",
        help="run an explicit one-shot stored session-window metadata receipt",
        description=(
            "Run one-shot stored session-window execution metadata from an "
            "explicit local schedule store, archive root, local clock, and "
            "same-invocation fixed confirmation response."
        ),
    )
    _add_session_window_execute_from_store_local_arguments(session_window_execution)
    session_window_execution.set_defaults(
        handler=_run_session_window_execute_from_store_local_command
    )

    session_window_start_receipt = subparsers.add_parser(
        "session-window-start-receipt-from-store-local",
        help="record an authorized stored session-window start receipt",
        description=(
            "Record metadata-only session-window start receipt data from an "
            "explicit read-only local schedule store, archive root, local clock, "
            "and fixed confirmation response."
        ),
    )
    _add_session_window_start_receipt_from_store_local_arguments(
        session_window_start_receipt
    )
    session_window_start_receipt.set_defaults(
        handler=_run_session_window_start_receipt_from_store_local_command
    )

    session_window_stop_execution_preflight = subparsers.add_parser(
        "session-window-stop-execution-preflight-from-store-local",
        help="preflight a stored session-window stop without writing",
        description=(
            "Build read-only stored session-window stop execution preflight "
            "metadata from an explicit read-only local schedule store, archive "
            "root, stored class time, and source kind."
        ),
    )
    _add_session_window_stop_execution_preflight_from_store_local_arguments(
        session_window_stop_execution_preflight
    )
    session_window_stop_execution_preflight.set_defaults(
        handler=_run_session_window_stop_execution_preflight_from_store_local_command
    )

    session_window_stop_execute = subparsers.add_parser(
        "session-window-stop-execute-from-store-local",
        help="run an explicit one-shot stored session-window stop receipt",
        description=(
            "Run one-shot stored session-window stop execution metadata from "
            "an explicit local schedule store, archive root, stored class "
            "time, source kind, and fixed confirmation response."
        ),
    )
    _add_session_window_stop_execute_from_store_local_arguments(
        session_window_stop_execute
    )
    session_window_stop_execute.set_defaults(
        handler=_run_session_window_stop_execute_from_store_local_command
    )

    session_window_stop_receipt = subparsers.add_parser(
        "session-window-stop-receipt-from-store-local",
        help="record a stored session-window stop receipt",
        description=(
            "Record metadata-only session-window stop receipt data from an "
            "explicit read-only local schedule store and existing runtime file."
        ),
    )
    _add_session_window_stop_receipt_from_store_local_arguments(
        session_window_stop_receipt
    )
    session_window_stop_receipt.set_defaults(
        handler=_run_session_window_stop_receipt_from_store_local_command
    )

    session_window_runtime_summary = subparsers.add_parser(
        "session-window-runtime-summary-local",
        help="summarize stored session-window runtime receipts",
        description=(
            "Build a read-only metadata summary from an existing stored "
            "session-window runtime file."
        ),
    )
    _add_session_window_runtime_summary_local_arguments(session_window_runtime_summary)
    session_window_runtime_summary.set_defaults(
        handler=_run_session_window_runtime_summary_local_command
    )

    session_window_recovery_decision = subparsers.add_parser(
        "session-window-recovery-decision-local",
        help="summarize stored session-window recovery decision metadata",
        description=(
            "Build a read-only stored session-window recovery decision from "
            "existing runtime and archive metadata."
        ),
    )
    _add_session_window_recovery_decision_local_arguments(
        session_window_recovery_decision
    )
    session_window_recovery_decision.set_defaults(
        handler=_run_session_window_recovery_decision_local_command
    )

    session_window_recovery_review = subparsers.add_parser(
        "session-window-recovery-review-local",
        help="summarize stored session-window recovery review metadata",
        description=(
            "Build a read-only stored session-window recovery review from "
            "existing recovery decision metadata."
        ),
    )
    _add_session_window_recovery_review_local_arguments(session_window_recovery_review)
    session_window_recovery_review.set_defaults(
        handler=_run_session_window_recovery_review_local_command
    )

    session_window_recovery_review_batch = subparsers.add_parser(
        "session-window-recovery-review-batch-local",
        help="summarize stored session-window recovery review batch metadata",
        description=(
            "Build a read-only stored session-window recovery review batch from "
            "explicit session identifiers."
        ),
    )
    _add_session_window_recovery_review_batch_local_arguments(
        session_window_recovery_review_batch
    )
    session_window_recovery_review_batch.set_defaults(
        handler=_run_session_window_recovery_review_batch_local_command
    )

    session_window_recovery_report = subparsers.add_parser(
        "session-window-recovery-report-local",
        help="render stored session-window recovery report metadata",
        description=(
            "Build a read-only stored session-window recovery report from "
            "explicit session identifiers."
        ),
    )
    _add_session_window_recovery_report_local_arguments(session_window_recovery_report)
    session_window_recovery_report.set_defaults(
        handler=_run_session_window_recovery_report_local_command
    )

    session_window_recovery_report_write = subparsers.add_parser(
        "session-window-recovery-report-write-local",
        help="write stored session-window recovery report metadata",
        description=(
            "Write a stored session-window recovery report file from explicit "
            "session identifiers."
        ),
    )
    _add_session_window_recovery_report_write_local_arguments(
        session_window_recovery_report_write
    )
    session_window_recovery_report_write.set_defaults(
        handler=_run_session_window_recovery_report_write_local_command
    )

    session_window_recovery_report_file_inventory = subparsers.add_parser(
        "session-window-recovery-report-file-inventory-local",
        help="inventory stored session-window recovery report file metadata",
        description=(
            "Inventory the fixed stored session-window recovery report file "
            "using local metadata only."
        ),
    )
    _add_session_window_recovery_report_file_inventory_local_arguments(
        session_window_recovery_report_file_inventory
    )
    session_window_recovery_report_file_inventory.set_defaults(
        handler=_run_session_window_recovery_report_file_inventory_local_command
    )

    session_window_recovery_report_file_verification = subparsers.add_parser(
        "session-window-recovery-report-file-verify-local",
        help="verify stored session-window recovery report file metadata",
        description=(
            "Verify the fixed stored session-window recovery report file "
            "against deterministic metadata for explicit session identifiers."
        ),
    )
    _add_session_window_recovery_report_file_verification_local_arguments(
        session_window_recovery_report_file_verification
    )
    session_window_recovery_report_file_verification.set_defaults(
        handler=_run_session_window_recovery_report_file_verification_local_command
    )

    session_window_recovery_report_file_action_preview = subparsers.add_parser(
        "session-window-recovery-report-file-action-preview-local",
        help="preview the next stored session-window recovery report file action",
        description=(
            "Preview the next safe local action for the fixed stored "
            "session-window recovery report file from verification metadata."
        ),
    )
    _add_session_window_recovery_report_file_action_preview_local_arguments(
        session_window_recovery_report_file_action_preview
    )
    session_window_recovery_report_file_action_preview.set_defaults(
        handler=_run_session_window_recovery_report_file_action_preview_local_command
    )

    session_window_recovery_report_file_action = subparsers.add_parser(
        "session-window-recovery-report-file-action-local",
        help="apply the next stored session-window recovery report file action",
        description=(
            "Apply the next safe local action for the fixed stored "
            "session-window recovery report file."
        ),
    )
    _add_session_window_recovery_report_file_action_local_arguments(
        session_window_recovery_report_file_action
    )
    session_window_recovery_report_file_action.set_defaults(
        handler=_run_session_window_recovery_report_file_action_local_command
    )

    session_window_recovery_report_file_status = subparsers.add_parser(
        "session-window-recovery-report-file-status-local",
        help="summarize stored session-window recovery report file status",
        description=(
            "Summarize the fixed stored session-window recovery report file "
            "status from verification metadata."
        ),
    )
    _add_session_window_recovery_report_file_status_local_arguments(
        session_window_recovery_report_file_status
    )
    session_window_recovery_report_file_status.set_defaults(
        handler=_run_session_window_recovery_report_file_status_local_command
    )

    subparsers.add_parser(
        "mic-recording-diagnostic",
        help="run the bounded microphone recording diagnostic",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv[:1] == ["mic-recording-diagnostic"]:
        return _run_mic_recording_diagnostic_command(argv[1:])
    if argv[:1] == ["crash-recovery-preflight"]:
        return _run_crash_recovery_preflight_argv(argv[1:])
    if "crash-recovery-preflight" in argv or any(
        arg == "--sessions-root" or arg.startswith("--sessions-root=") for arg in argv
    ):
        print(_CRASH_RECOVERY_PREFLIGHT_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["archive-delete-dry-run-local"]:
        return _run_archive_delete_dry_run_local_argv(argv[1:])
    if "archive-delete-dry-run-local" in argv:
        print(_ARCHIVE_DELETE_DRY_RUN_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["gate-d-readiness-local"]:
        return _run_gate_d_readiness_local_argv(argv[1:])
    if argv[:1] == ["gate-d-evidence-gaps-local"]:
        return _run_gate_d_evidence_gaps_local_argv(argv[1:])
    if "gate-d-evidence-gaps-local" in argv:
        print(_GATE_D_EVIDENCE_GAP_SUMMARY_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["alert-routing-smoke-local"]:
        return _run_alert_routing_smoke_local_argv(argv[1:])
    if "alert-routing-smoke-local" in argv or any(
        arg == "--event-type" or arg.startswith("--event-type=") for arg in argv
    ):
        print(_ALERT_ROUTING_SMOKE_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["policy-gate-smoke-local"]:
        return _run_policy_gate_smoke_local_argv(argv[1:])
    if "policy-gate-smoke-local" in argv:
        print(_POLICY_GATE_SMOKE_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["delivery-path-smoke-local"]:
        return _run_delivery_path_smoke_local_argv(argv[1:])
    if "delivery-path-smoke-local" in argv:
        print(_DELIVERY_PATH_SMOKE_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["monitoring-boundary-smoke-local"]:
        return _run_monitoring_boundary_smoke_local_argv(argv[1:])
    if "monitoring-boundary-smoke-local" in argv:
        print(_MONITORING_BOUNDARY_SMOKE_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["gate-d-security-review-evidence-local"]:
        return _run_gate_d_security_review_evidence_local_argv(argv[1:])
    if "gate-d-security-review-evidence-local" in argv:
        print(_GATE_D_SECURITY_REVIEW_EVIDENCE_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["gate-d-mic-diagnostics-after-reboot-evidence-local"]:
        return _run_gate_d_mic_diagnostics_after_reboot_evidence_local_argv(argv[1:])
    if "gate-d-mic-diagnostics-after-reboot-evidence-local" in argv:
        print(
            _GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if argv[:1] == ["gate-d-signal-quality-evidence-local"]:
        return _run_gate_d_signal_quality_evidence_local_argv(argv[1:])
    if "gate-d-signal-quality-evidence-local" in argv:
        print(_GATE_D_SIGNAL_QUALITY_EVIDENCE_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["gate-d-product-judgment-evidence-local"]:
        return _run_gate_d_product_judgment_evidence_local_argv(argv[1:])
    if "gate-d-product-judgment-evidence-local" in argv:
        print(_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["gate-d-scheduler-lifecycle-evidence-local"]:
        return _run_gate_d_scheduler_lifecycle_evidence_local_argv(argv[1:])
    if "gate-d-scheduler-lifecycle-evidence-local" in argv:
        print(_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["gate-d-rollback-plan-evidence-local"]:
        return _run_gate_d_rollback_plan_evidence_local_argv(argv[1:])
    if "gate-d-rollback-plan-evidence-local" in argv:
        print(_GATE_D_ROLLBACK_PLAN_EVIDENCE_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["gate-d-local-evidence-bundle"]:
        return _run_gate_d_local_evidence_bundle_argv(argv[1:])
    if "gate-d-local-evidence-bundle" in argv:
        print(_GATE_D_LOCAL_EVIDENCE_BUNDLE_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["session-window-lifecycle-smoke-local"]:
        return _run_session_window_lifecycle_smoke_local_argv(argv[1:])
    if "session-window-lifecycle-smoke-local" in argv:
        print(_SESSION_WINDOW_LIFECYCLE_SMOKE_CLI_ERROR, file=sys.stderr)
        return 2
    if "gate-d-readiness-local" in argv or any(
        arg == "--mic-diagnostics-after-reboot"
        or arg.startswith("--mic-diagnostics-after-reboot=")
        or arg == "--alert-routing"
        or arg.startswith("--alert-routing=")
        or arg == "--security-review"
        or arg.startswith("--security-review=")
        or arg == "--policy-gate-tests"
        or arg.startswith("--policy-gate-tests=")
        or arg == "--rollback-plan-for-loopback-playwright-spike"
        or arg.startswith("--rollback-plan-for-loopback-playwright-spike=")
        or arg == "--signal-quality-evidence"
        or arg.startswith("--signal-quality-evidence=")
        or arg == "--scheduler-lifecycle-evidence"
        or arg.startswith("--scheduler-lifecycle-evidence=")
        or arg == "--delivery-path-evidence"
        or arg.startswith("--delivery-path-evidence=")
        or arg == "--monitoring-boundary-evidence"
        or arg.startswith("--monitoring-boundary-evidence=")
        or arg == "--product-judgment-evidence"
        or arg.startswith("--product-judgment-evidence=")
        for arg in argv
    ):
        print(_GATE_D_READINESS_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["scheduled-start-preview-local"]:
        return _run_scheduled_start_preview_local_argv(argv[1:])
    if argv[:1] == ["scheduled-start-preview-from-store-local"]:
        return _run_scheduled_start_preview_from_store_local_argv(argv[1:])
    if argv[:1] == ["scheduled-start-next-from-store-local"]:
        return _run_scheduled_start_next_from_store_local_argv(argv[1:])
    if argv[:1] == ["scheduled-start-due-list-from-store-local"]:
        return _run_scheduled_start_due_list_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-stop-preview-from-store-local"]:
        return _run_session_stop_preview_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-plan-from-store-local"]:
        return _run_session_window_plan_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-archive-preflight-from-store-local"]:
        return _run_session_window_archive_preflight_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-alert-preview-from-store-local"]:
        return _run_session_window_alert_preview_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-readiness-preflight-from-store-local"]:
        return _run_session_window_readiness_preflight_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-confirmation-preflight-from-store-local"]:
        return _run_session_window_confirmation_preflight_from_store_local_argv(
            argv[1:]
        )
    if argv[:1] == ["session-window-confirmation-response-from-store-local"]:
        return _run_session_window_confirmation_response_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-start-authorization-from-store-local"]:
        return _run_session_window_start_authorization_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-execution-preflight-from-store-local"]:
        return _run_session_window_execution_preflight_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-execute-from-store-local"]:
        return _run_session_window_execute_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-start-receipt-from-store-local"]:
        return _run_session_window_start_receipt_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-stop-execution-preflight-from-store-local"]:
        return _run_session_window_stop_execution_preflight_from_store_local_argv(
            argv[1:]
        )
    if argv[:1] == ["session-window-stop-execute-from-store-local"]:
        return _run_session_window_stop_execute_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-stop-receipt-from-store-local"]:
        return _run_session_window_stop_receipt_from_store_local_argv(argv[1:])
    if argv[:1] == ["session-window-runtime-summary-local"]:
        return _run_session_window_runtime_summary_local_argv(argv[1:])
    if argv[:1] == ["session-window-recovery-decision-local"]:
        return _run_session_window_recovery_decision_local_argv(argv[1:])
    if argv[:1] == ["session-window-recovery-review-local"]:
        return _run_session_window_recovery_review_local_argv(argv[1:])
    if argv[:1] == ["session-window-recovery-review-batch-local"]:
        return _run_session_window_recovery_review_batch_local_argv(argv[1:])
    if argv[:1] == ["session-window-recovery-report-local"]:
        return _run_session_window_recovery_report_local_argv(argv[1:])
    if argv[:1] == ["session-window-recovery-report-write-local"]:
        return _run_session_window_recovery_report_write_local_argv(argv[1:])
    if argv[:1] == ["session-window-recovery-report-file-inventory-local"]:
        return _run_session_window_recovery_report_file_inventory_local_argv(argv[1:])
    if argv[:1] == ["session-window-recovery-report-file-verify-local"]:
        return _run_session_window_recovery_report_file_verification_local_argv(
            argv[1:]
        )
    if argv[:1] == ["session-window-recovery-report-file-action-preview-local"]:
        return _run_session_window_recovery_report_file_action_preview_local_argv(
            argv[1:]
        )
    if argv[:1] == ["session-window-recovery-report-file-action-local"]:
        return _run_session_window_recovery_report_file_action_local_argv(argv[1:])
    if argv[:1] == ["session-window-recovery-report-file-status-local"]:
        return _run_session_window_recovery_report_file_status_local_argv(argv[1:])
    if argv[:1] == ["course-schedule-save-local"]:
        return _run_course_schedule_save_local_argv(argv[1:])
    if argv[:1] == ["course-schedule-summary-local"]:
        return _run_course_schedule_summary_local_argv(argv[1:])
    if argv[:1] == ["course-schedule-list-local"]:
        return _run_course_schedule_list_local_argv(argv[1:])
    if "course-schedule-list-local" in argv:
        print(_COURSE_SCHEDULE_LIST_CLI_ERROR, file=sys.stderr)
        return 2
    if "course-schedule-save-local" in argv or any(
        arg == "--class-time"
        or arg.startswith("--class-time=")
        or arg == "--title"
        or arg.startswith("--title=")
        or arg == "--instructor-name"
        or arg.startswith("--instructor-name=")
        or arg == "--meeting-url"
        or arg.startswith("--meeting-url=")
        or arg == "--meeting-label"
        or arg.startswith("--meeting-label=")
        for arg in argv
    ):
        print(_COURSE_SCHEDULE_SAVE_CLI_ERROR, file=sys.stderr)
        return 2
    if "scheduled-start-next-from-store-local" in argv:
        print(_SCHEDULED_START_NEXT_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 2
    if "scheduled-start-due-list-from-store-local" in argv:
        print(_SCHEDULED_START_DUE_LIST_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 2
    if "session-stop-preview-from-store-local" in argv:
        print(_SESSION_STOP_PREVIEW_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 2
    if "session-window-plan-from-store-local" in argv:
        print(_SESSION_WINDOW_PLAN_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 2
    if "session-window-archive-preflight-from-store-local" in argv:
        print(
            _SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-alert-preview-from-store-local" in argv:
        print(
            _SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-readiness-preflight-from-store-local" in argv:
        print(
            _SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-confirmation-preflight-from-store-local" in argv:
        print(
            _SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-confirmation-response-from-store-local" in argv:
        print(
            _SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-start-authorization-from-store-local" in argv:
        print(
            _SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-execution-preflight-from-store-local" in argv:
        print(
            _SESSION_WINDOW_EXECUTION_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-execute-from-store-local" in argv:
        print(
            _SESSION_WINDOW_EXECUTION_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-start-receipt-from-store-local" in argv:
        print(
            _SESSION_WINDOW_START_RECEIPT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-stop-execution-preflight-from-store-local" in argv:
        print(
            _SESSION_WINDOW_STOP_EXECUTION_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-stop-execute-from-store-local" in argv:
        print(
            _SESSION_WINDOW_STOP_EXECUTION_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-stop-receipt-from-store-local" in argv:
        print(
            _SESSION_WINDOW_STOP_RECEIPT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-runtime-summary-local" in argv:
        print(
            _SESSION_WINDOW_RUNTIME_SUMMARY_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-recovery-decision-local" in argv:
        print(
            _SESSION_WINDOW_RECOVERY_DECISION_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-recovery-review-local" in argv:
        print(
            _SESSION_WINDOW_RECOVERY_REVIEW_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-recovery-review-batch-local" in argv:
        print(
            _SESSION_WINDOW_RECOVERY_REVIEW_BATCH_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-recovery-report-local" in argv:
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-recovery-report-write-local" in argv:
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-recovery-report-file-inventory-local" in argv:
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_INVENTORY_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-recovery-report-file-verify-local" in argv:
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_VERIFICATION_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-recovery-report-file-action-preview-local" in argv:
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_PREVIEW_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-recovery-report-file-action-local" in argv:
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "session-window-recovery-report-file-status-local" in argv:
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_STATUS_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if any(
        arg == "--archive-root" or arg.startswith("--archive-root=") for arg in argv
    ) and any(arg == "--db-path" or arg.startswith("--db-path=") for arg in argv):
        print(
            _SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 2
    if "scheduled-start-preview-from-store-local" in argv or any(
        arg == "--class-time-index" or arg.startswith("--class-time-index=")
        for arg in argv
    ):
        print(_SCHEDULED_START_PREVIEW_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 2
    if "course-schedule-summary-local" in argv or any(
        arg == "--db-path" or arg.startswith("--db-path=") for arg in argv
    ):
        print(_COURSE_SCHEDULE_SUMMARY_CLI_ERROR, file=sys.stderr)
        return 2
    if "scheduled-start-preview-local" in argv or any(
        arg == "--course-id"
        or arg.startswith("--course-id=")
        or arg == "--day-of-week"
        or arg.startswith("--day-of-week=")
        or arg == "--local-start-time"
        or arg.startswith("--local-start-time=")
        or arg == "--duration-minutes"
        or arg.startswith("--duration-minutes=")
        or arg == "--source-kind"
        or arg.startswith("--source-kind=")
        or arg == "--clock-day-of-week"
        or arg.startswith("--clock-day-of-week=")
        or arg == "--clock-local-time"
        or arg.startswith("--clock-local-time=")
        or arg == "--disabled"
        for arg in argv
    ):
        print(_SCHEDULED_START_PREVIEW_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["archive-export-preflight"]:
        return _run_archive_export_preflight_argv(argv[1:])
    if argv[:1] == ["archive-export-verify-local"]:
        return _run_archive_export_verify_local_argv(argv[1:])
    if "archive-export-verify-local" in argv:
        print(_ARCHIVE_EXPORT_VERIFY_CLI_ERROR, file=sys.stderr)
        return 2
    if argv[:1] == ["archive-export-local"]:
        return _run_archive_export_local_argv(argv[1:])
    if "archive-export-local" in argv or any(
        arg == "--export-root" or arg.startswith("--export-root=") for arg in argv
    ):
        print(_ARCHIVE_EXPORT_CLI_ERROR, file=sys.stderr)
        return 2
    if "archive-export-preflight" in argv or any(
        arg == "--archive-root" or arg.startswith("--archive-root=") for arg in argv
    ):
        print(_ARCHIVE_EXPORT_PREFLIGHT_CLI_ERROR, file=sys.stderr)
        return 2

    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        return 0
    return handler(args)


def _add_crash_recovery_preflight_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe session identifier to inspect",
    )
    parser.add_argument(
        "--sessions-root",
        type=Path,
        required=True,
        help="explicit root directory containing session artifact directories",
    )


def _add_archive_export_preflight_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe session identifier to inspect",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit root directory containing session archive directories",
    )


def _add_archive_export_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe session identifier to export",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit root directory containing session archive directories",
    )
    parser.add_argument(
        "--export-root",
        type=Path,
        required=True,
        help="explicit existing local root directory for copied export artifacts",
    )


def _add_archive_export_verify_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe session identifier to verify",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit root directory containing session archive directories",
    )
    parser.add_argument(
        "--export-root",
        type=Path,
        required=True,
        help="explicit existing local root directory containing exported artifacts",
    )


def _add_archive_delete_dry_run_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe session identifier to inspect",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit root directory containing session archive directories",
    )


def _add_gate_d_readiness_local_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--mic-diagnostics-after-reboot",
        required=True,
        choices=_GATE_D_READINESS_STATUSES,
        help="fixed scalar status for reboot-era mic diagnostic evidence",
    )
    parser.add_argument(
        "--alert-routing",
        required=True,
        choices=_GATE_D_READINESS_STATUSES,
        help="fixed scalar status for alert-routing readiness evidence",
    )
    parser.add_argument(
        "--security-review",
        required=True,
        choices=_GATE_D_READINESS_STATUSES,
        help="fixed scalar status for security review evidence",
    )
    parser.add_argument(
        "--policy-gate-tests",
        required=True,
        choices=_GATE_D_READINESS_STATUSES,
        help="fixed scalar status for policy gate test evidence",
    )
    parser.add_argument(
        "--rollback-plan-for-loopback-playwright-spike",
        required=True,
        choices=_GATE_D_READINESS_STATUSES,
        help="fixed scalar status for rollback-plan readiness evidence",
    )
    parser.add_argument(
        "--signal-quality-evidence",
        default="missing",
        choices=_GATE_D_READINESS_STATUSES,
        help="fixed scalar status for signal quality evidence",
    )
    parser.add_argument(
        "--scheduler-lifecycle-evidence",
        default="missing",
        choices=_GATE_D_READINESS_STATUSES,
        help="fixed scalar status for scheduler lifecycle evidence",
    )
    parser.add_argument(
        "--delivery-path-evidence",
        default="missing",
        choices=_GATE_D_READINESS_STATUSES,
        help="fixed scalar status for delivery path evidence",
    )
    parser.add_argument(
        "--monitoring-boundary-evidence",
        default="missing",
        choices=_GATE_D_READINESS_STATUSES,
        help="fixed scalar status for monitoring boundary evidence",
    )
    parser.add_argument(
        "--product-judgment-evidence",
        default="missing",
        choices=_GATE_D_READINESS_STATUSES,
        help="fixed scalar status for product judgment evidence",
    )


def _add_alert_routing_smoke_local_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--event-type",
        required=True,
        help="controlled lecture event type for the local smoke",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="build disabled metadata without calling the local dispatcher",
    )


def _add_session_window_lifecycle_smoke_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit local archive root",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled lifecycle smoke metadata without writing local state",
    )


def _add_scheduled_start_preview_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier to preview",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier for the preview",
    )
    parser.add_argument(
        "--day-of-week",
        required=True,
        help="scheduled weekday name",
    )
    parser.add_argument(
        "--local-start-time",
        required=True,
        help="scheduled local start time in HH:MM",
    )
    parser.add_argument(
        "--duration-minutes",
        required=True,
        type=int,
        help="scheduled class duration in minutes",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preview",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="preview the schedule as disabled",
    )


def _add_course_schedule_summary_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to summarize",
    )


def _add_course_schedule_list_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )


def _add_course_schedule_save_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit local SQLite course schedule database",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to save",
    )
    parser.add_argument(
        "--title",
        required=True,
        help="course title to validate and store locally",
    )
    parser.add_argument(
        "--instructor-name",
        help="optional instructor name to validate and store locally",
    )
    parser.add_argument(
        "--meeting-url",
        help="optional meeting URL to validate and store locally",
    )
    parser.add_argument(
        "--meeting-label",
        help="optional meeting label to validate and store locally",
    )
    parser.add_argument(
        "--class-time",
        action="append",
        required=True,
        metavar="DAY,HH:MM,DURATION[,TIMEZONE][,LABEL]",
        help="repeatable class time metadata to validate and store locally",
    )


def _add_scheduled_start_preview_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier to preview",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to preview",
    )
    parser.add_argument(
        "--class-time-index",
        required=True,
        type=int,
        help="explicit zero-based stored class-time index to preview",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preview",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="preview the stored schedule as disabled",
    )


def _add_scheduled_start_next_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier to preview",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to preview",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preview",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="preview the next stored schedule as disabled",
    )


def _add_scheduled_start_due_list_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the due list",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preview",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled due-list metadata without due courses",
    )


def _add_session_stop_preview_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to preview",
    )
    parser.add_argument(
        "--class-time-index",
        required=True,
        type=int,
        help="explicit zero-based stored class-time index to preview",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preview",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="preview the stored session stop as disabled",
    )


def _add_session_window_plan_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the session window plan",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to plan",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window metadata without due courses",
    )


def _add_session_window_archive_preflight_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the archive preflight",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit archive root containing the safe session directory",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preflight",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window archive metadata without due courses",
    )


def _add_session_window_alert_preview_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the alert preview",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preview",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window alert metadata without due courses",
    )


def _add_session_window_readiness_preflight_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the readiness preflight",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit archive root containing the safe session directory",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preflight",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window readiness metadata without due courses",
    )


def _add_session_window_confirmation_preflight_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the confirmation preflight",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit archive root containing the safe session directory",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preflight",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window confirmation metadata without due courses",
    )


def _add_session_window_confirmation_response_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the confirmation response",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit archive root containing the safe session directory",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preflight",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--confirmation-response",
        required=True,
        choices=("confirmed", "declined"),
        help="fixed user response token to record",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window response metadata without due courses",
    )


def _add_session_window_start_authorization_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the start authorization",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit archive root containing the safe session directory",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to authorize",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--confirmation-response",
        required=True,
        choices=("confirmed", "declined"),
        help="fixed user response token to authorize",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window authorization metadata without starts",
    )


def _add_session_window_execution_preflight_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the execution preflight",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit archive root containing the safe session directory",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to preflight",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--confirmation-response",
        required=True,
        choices=("confirmed", "declined"),
        help="same-invocation fixed user confirmation response token",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window execution metadata without starts",
    )


def _add_session_window_execute_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the one-shot execution",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root for the one-shot receipt",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to record as metadata",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--confirmation-response",
        required=True,
        choices=("confirmed", "declined"),
        help="same-invocation fixed user confirmation response token",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled one-shot execution metadata without writing",
    )


def _add_session_window_start_receipt_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the start receipt",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root for the runtime receipt",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to record",
    )
    parser.add_argument(
        "--clock-day-of-week",
        required=True,
        help="explicit local clock weekday name",
    )
    parser.add_argument(
        "--clock-local-time",
        required=True,
        help="explicit local clock time in HH:MM",
    )
    parser.add_argument(
        "--confirmation-response",
        required=True,
        choices=("confirmed", "declined"),
        help="fixed user response token to record",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window receipt metadata without writing",
    )


def _add_session_window_stop_execution_preflight_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the stop preflight",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root for runtime metadata",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to inspect",
    )
    parser.add_argument(
        "--class-time-index",
        required=True,
        type=int,
        help="explicit zero-based stored class-time index to inspect",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to inspect as metadata",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window stop preflight metadata",
    )


def _add_session_window_stop_execute_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the stop execution",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root for runtime metadata",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to inspect",
    )
    parser.add_argument(
        "--class-time-index",
        required=True,
        type=int,
        help="explicit zero-based stored class-time index to inspect",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to inspect as metadata",
    )
    parser.add_argument(
        "--confirmation-response",
        required=True,
        choices=("confirmed", "declined"),
        help="fixed user response token to record",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window stop execution metadata",
    )


def _add_session_window_stop_receipt_from_store_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the stop receipt",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        required=True,
        help="explicit existing local SQLite course schedule database",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root for the runtime receipt",
    )
    parser.add_argument(
        "--course-id",
        required=True,
        help="safe course identifier to record",
    )
    parser.add_argument(
        "--class-time-index",
        required=True,
        type=int,
        help="explicit zero-based stored class-time index to record",
    )
    parser.add_argument(
        "--source-kind",
        required=True,
        choices=("file", "mic"),
        help="local source kind to record",
    )
    parser.add_argument(
        "--disabled",
        action="store_true",
        help="return disabled session-window stop receipt metadata without writing",
    )


def _add_session_window_runtime_summary_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the runtime summary",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root containing runtime metadata",
    )


def _add_session_window_recovery_decision_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the recovery decision",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root containing session metadata",
    )


def _add_session_window_recovery_review_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_id",
        help="safe local session identifier for the recovery review",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root containing session metadata",
    )


def _add_session_window_recovery_review_batch_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_ids",
        nargs="+",
        help="one or more safe local session identifiers for the recovery review batch",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root containing session metadata",
    )


def _add_session_window_recovery_report_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_ids",
        nargs="+",
        help="one or more safe local session identifiers for the recovery report",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root containing session metadata",
    )


def _add_session_window_recovery_report_write_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_ids",
        nargs="+",
        help="one or more safe local session identifiers for the recovery report file",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root containing session metadata",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="explicit existing local output root for the recovery report file",
    )


def _add_session_window_recovery_report_file_inventory_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root for containment checks",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="explicit existing local output root containing the report file",
    )


def _add_session_window_recovery_report_file_verification_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    parser.add_argument(
        "session_ids",
        nargs="+",
        help="one or more safe local session identifiers for the recovery report",
    )
    parser.add_argument(
        "--archive-root",
        type=Path,
        required=True,
        help="explicit existing local archive root containing session metadata",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="explicit existing local output root containing the report file",
    )


def _add_session_window_recovery_report_file_action_preview_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    _add_session_window_recovery_report_file_verification_local_arguments(parser)


def _add_session_window_recovery_report_file_action_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    _add_session_window_recovery_report_file_verification_local_arguments(parser)


def _add_session_window_recovery_report_file_status_local_arguments(
    parser: argparse.ArgumentParser,
) -> None:
    _add_session_window_recovery_report_file_verification_local_arguments(parser)


def _run_fixture_demo_command(args: argparse.Namespace) -> int:
    result = run_fixture_demo(
        args.fixture_path,
        output_root=args.output_root,
    )
    paths = result.artifact_paths

    print("Fixture demo complete.")
    print(f"Session: {result.session_id}")
    print(f"Segments loaded: {result.segment_count}")
    print(f"Events detected: {result.event_count}")
    print(f"Output directory: {paths.output_dir}")
    print(f"Events JSONL: {paths.events_path}")
    print(f"Fake alert log: {paths.alerts_path}")
    print(f"Reviewer: {paths.reviewer_path}")
    return 0


def _run_crash_recovery_preflight_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar crash-recovery-preflight",
        description=(
            "Summarize read-only crash-recovery metadata for one explicit session root."
        ),
        fixed_error_message=_CRASH_RECOVERY_PREFLIGHT_CLI_ERROR,
    )
    _add_crash_recovery_preflight_arguments(parser)
    args = parser.parse_args(argv)
    return _run_crash_recovery_preflight_command(args)


def _run_crash_recovery_preflight_command(args: argparse.Namespace) -> int:
    from async_scholar.session_recovery import (
        CRASH_RECOVERY_PREFLIGHT_ERROR,
        build_crash_recovery_session_preflight,
        crash_recovery_session_preflight_safe_summary,
    )

    try:
        preflight = build_crash_recovery_session_preflight(
            args.sessions_root,
            args.session_id,
        )
        payload = crash_recovery_session_preflight_safe_summary(preflight)
    except ValueError:
        print(CRASH_RECOVERY_PREFLIGHT_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_archive_export_preflight_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar archive-export-preflight",
        description=(
            "Summarize read-only archive export metadata for one explicit "
            "session archive root."
        ),
        fixed_error_message=_ARCHIVE_EXPORT_PREFLIGHT_CLI_ERROR,
    )
    _add_archive_export_preflight_arguments(parser)
    args = parser.parse_args(argv)
    return _run_archive_export_preflight_command(args)


def _run_archive_export_preflight_command(args: argparse.Namespace) -> int:
    from async_scholar.archive_export import (
        archive_export_preflight_summary_safe_summary,
        build_archive_export_preflight_summary_from_root,
    )

    try:
        preflight = build_archive_export_preflight_summary_from_root(
            args.archive_root,
            args.session_id,
        )
        payload = archive_export_preflight_summary_safe_summary(preflight)
    except ValueError:
        print(_ARCHIVE_EXPORT_PREFLIGHT_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_archive_export_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar archive-export-local",
        description=(
            "Copy allowlisted archive artifacts for one explicit local session "
            "archive root to one explicit existing local export root."
        ),
        fixed_error_message=_ARCHIVE_EXPORT_CLI_ERROR,
    )
    _add_archive_export_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_archive_export_local_command(args)


def _run_archive_export_local_command(args: argparse.Namespace) -> int:
    from async_scholar.archive_export import (
        archive_export_execution_result_safe_summary,
        execute_archive_export_to_local_root,
    )

    try:
        export_result = execute_archive_export_to_local_root(
            args.archive_root,
            args.export_root,
            args.session_id,
        )
        payload = archive_export_execution_result_safe_summary(export_result)
    except ValueError:
        print(_ARCHIVE_EXPORT_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_archive_export_verify_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar archive-export-verify-local",
        description=(
            "Verify allowlisted archive export metadata for one explicit local "
            "session archive root and one explicit existing local export root."
        ),
        fixed_error_message=_ARCHIVE_EXPORT_VERIFY_CLI_ERROR,
    )
    _add_archive_export_verify_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_archive_export_verify_local_command(args)


def _run_archive_export_verify_local_command(args: argparse.Namespace) -> int:
    from async_scholar.archive_export import (
        archive_export_verification_summary_safe_summary,
        build_archive_export_verification_summary_from_roots,
    )

    try:
        verification = build_archive_export_verification_summary_from_roots(
            args.archive_root,
            args.export_root,
            args.session_id,
        )
        payload = archive_export_verification_summary_safe_summary(verification)
    except ValueError:
        print(_ARCHIVE_EXPORT_VERIFY_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_archive_delete_dry_run_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar archive-delete-dry-run-local",
        description=(
            "Summarize a read-only local archive delete dry run for one "
            "explicit session archive root."
        ),
        fixed_error_message=_ARCHIVE_DELETE_DRY_RUN_CLI_ERROR,
    )
    _add_archive_delete_dry_run_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_archive_delete_dry_run_local_command(args)


def _run_archive_delete_dry_run_local_command(args: argparse.Namespace) -> int:
    from async_scholar.archive_delete_dry_run_result import (
        ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR,
        build_archive_delete_dry_run_local_result,
        export_archive_delete_dry_run_local_result,
    )

    try:
        dry_run = build_archive_delete_dry_run_local_result(
            args.archive_root,
            args.session_id,
        )
        payload = export_archive_delete_dry_run_local_result(dry_run)
    except ValueError:
        print(ARCHIVE_DELETE_DRY_RUN_LOCAL_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_gate_d_readiness_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar gate-d-readiness-local",
        description=(
            "Build a metadata-only Gate D readiness report from explicit scalar "
            "evidence status flags."
        ),
        fixed_error_message=_GATE_D_READINESS_CLI_ERROR,
    )
    _add_gate_d_readiness_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_gate_d_readiness_local_command(args)


def _run_gate_d_readiness_local_command(args: argparse.Namespace) -> int:
    try:
        from async_scholar.gate_d_readiness import build_gate_d_readiness_report

        payload = build_gate_d_readiness_report(
            mic_diagnostics_after_reboot=args.mic_diagnostics_after_reboot,
            alert_routing=args.alert_routing,
            security_review=args.security_review,
            policy_gate_tests=args.policy_gate_tests,
            rollback_plan_for_loopback_playwright_spike=(
                args.rollback_plan_for_loopback_playwright_spike
            ),
            signal_quality_evidence=args.signal_quality_evidence,
            scheduler_lifecycle_evidence=args.scheduler_lifecycle_evidence,
            delivery_path_evidence=args.delivery_path_evidence,
            monitoring_boundary_evidence=args.monitoring_boundary_evidence,
            product_judgment_evidence=args.product_judgment_evidence,
        )
    except (ImportError, KeyError, TypeError, ValueError):
        print(_GATE_D_READINESS_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_gate_d_evidence_gaps_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar gate-d-evidence-gaps-local",
        description=(
            "Build a metadata-only Gate D evidence gap summary from explicit "
            "scalar evidence status flags."
        ),
        fixed_error_message=_GATE_D_EVIDENCE_GAP_SUMMARY_CLI_ERROR,
    )
    _add_gate_d_readiness_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_gate_d_evidence_gaps_local_command(args)


def _run_gate_d_evidence_gaps_local_command(args: argparse.Namespace) -> int:
    try:
        from async_scholar.gate_d_readiness import build_gate_d_evidence_gap_summary

        payload = build_gate_d_evidence_gap_summary(
            mic_diagnostics_after_reboot=args.mic_diagnostics_after_reboot,
            alert_routing=args.alert_routing,
            security_review=args.security_review,
            policy_gate_tests=args.policy_gate_tests,
            rollback_plan_for_loopback_playwright_spike=(
                args.rollback_plan_for_loopback_playwright_spike
            ),
            signal_quality_evidence=args.signal_quality_evidence,
            scheduler_lifecycle_evidence=args.scheduler_lifecycle_evidence,
            delivery_path_evidence=args.delivery_path_evidence,
            monitoring_boundary_evidence=args.monitoring_boundary_evidence,
            product_judgment_evidence=args.product_judgment_evidence,
        )
    except (ImportError, KeyError, TypeError, ValueError):
        print(_GATE_D_EVIDENCE_GAP_SUMMARY_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_alert_routing_smoke_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar alert-routing-smoke-local",
        description=(
            "Route one controlled local alert through the existing in-process "
            "dispatch boundary."
        ),
        fixed_error_message=_ALERT_ROUTING_SMOKE_CLI_ERROR,
    )
    _add_alert_routing_smoke_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_alert_routing_smoke_local_command(args)


def _run_alert_routing_smoke_local_command(args: argparse.Namespace) -> int:
    from async_scholar.alert_routing_smoke import build_local_alert_routing_smoke

    try:
        payload = build_local_alert_routing_smoke(
            args.event_type,
            disabled=args.disabled,
        )
    except (KeyError, RuntimeError, TypeError, ValueError):
        print(_ALERT_ROUTING_SMOKE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_policy_gate_smoke_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar policy-gate-smoke-local",
        description=(
            "Build a metadata-only local policy-gate smoke summary from fixed "
            "synthetic checks."
        ),
        fixed_error_message=_POLICY_GATE_SMOKE_CLI_ERROR,
    )
    args = parser.parse_args(argv)
    return _run_policy_gate_smoke_local_command(args)


def _run_policy_gate_smoke_local_command(args: argparse.Namespace) -> int:
    from async_scholar.policy_gate_smoke import build_local_policy_gate_smoke

    try:
        payload = build_local_policy_gate_smoke()
    except (KeyError, RuntimeError, TypeError, ValueError):
        print(_POLICY_GATE_SMOKE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_delivery_path_smoke_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar delivery-path-smoke-local",
        description=(
            "Build a metadata-only local delivery-path smoke summary from fixed "
            "synthetic checks."
        ),
        fixed_error_message=_DELIVERY_PATH_SMOKE_CLI_ERROR,
    )
    args = parser.parse_args(argv)
    return _run_delivery_path_smoke_local_command(args)


def _run_delivery_path_smoke_local_command(args: argparse.Namespace) -> int:
    try:
        from async_scholar.delivery_path_smoke import build_local_delivery_path_smoke

        payload = build_local_delivery_path_smoke()
    except (ImportError, KeyError, RuntimeError, TypeError, ValueError):
        print(_DELIVERY_PATH_SMOKE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_monitoring_boundary_smoke_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar monitoring-boundary-smoke-local",
        description=(
            "Build a metadata-only local monitoring-boundary smoke summary "
            "from fixed synthetic checks."
        ),
        fixed_error_message=_MONITORING_BOUNDARY_SMOKE_CLI_ERROR,
    )
    args = parser.parse_args(argv)
    return _run_monitoring_boundary_smoke_local_command(args)


def _run_monitoring_boundary_smoke_local_command(args: argparse.Namespace) -> int:
    try:
        from async_scholar.monitoring_boundary_smoke import (
            build_local_monitoring_boundary_smoke,
        )

        payload = build_local_monitoring_boundary_smoke()
    except (ImportError, KeyError, RuntimeError, TypeError, ValueError):
        print(_MONITORING_BOUNDARY_SMOKE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_gate_d_security_review_evidence_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar gate-d-security-review-evidence-local",
        description=(
            "Build a metadata-only local Gate D security-review evidence summary "
            "from fixed checks."
        ),
        fixed_error_message=_GATE_D_SECURITY_REVIEW_EVIDENCE_CLI_ERROR,
    )
    args = parser.parse_args(argv)
    return _run_gate_d_security_review_evidence_local_command(args)


def _run_gate_d_security_review_evidence_local_command(
    args: argparse.Namespace,
) -> int:
    try:
        from async_scholar.gate_d_security_review_evidence import (
            build_local_gate_d_security_review_evidence,
        )

        payload = build_local_gate_d_security_review_evidence()
        output = _gate_d_security_review_evidence_json(payload)
    except (ImportError, KeyError, RuntimeError, TypeError, ValueError):
        print(_GATE_D_SECURITY_REVIEW_EVIDENCE_CLI_ERROR, file=sys.stderr)
        return 1

    print(output)
    return 0


def _gate_d_security_review_evidence_json(payload: object) -> str:
    if (
        type(payload) is not dict
        or tuple(payload) != _GATE_D_SECURITY_REVIEW_EVIDENCE_KEYS
    ):
        raise ValueError(_GATE_D_SECURITY_REVIEW_EVIDENCE_CLI_ERROR)
    if payload["evidence_kind"] != "local_gate_d_security_review_evidence":
        raise ValueError(_GATE_D_SECURITY_REVIEW_EVIDENCE_CLI_ERROR)
    for key, expected in _GATE_D_SECURITY_REVIEW_EVIDENCE_STATUSES.items():
        if payload[key] != expected:
            raise ValueError(_GATE_D_SECURITY_REVIEW_EVIDENCE_CLI_ERROR)
    if any(
        payload[flag] is not False
        for flag in _GATE_D_SECURITY_REVIEW_EVIDENCE_FALSE_FLAGS
    ):
        raise ValueError(_GATE_D_SECURITY_REVIEW_EVIDENCE_CLI_ERROR)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _run_gate_d_mic_diagnostics_after_reboot_evidence_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar gate-d-mic-diagnostics-after-reboot-evidence-local",
        description=(
            "Build a metadata-only local Gate D mic diagnostics after-reboot "
            "evidence summary from fixed checks."
        ),
        fixed_error_message=_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_CLI_ERROR,
    )
    args = parser.parse_args(argv)
    return _run_gate_d_mic_diagnostics_after_reboot_evidence_local_command(args)


def _run_gate_d_mic_diagnostics_after_reboot_evidence_local_command(
    args: argparse.Namespace,
) -> int:
    try:
        from async_scholar.gate_d_mic_diagnostics_after_reboot_evidence import (
            build_local_gate_d_mic_diagnostics_after_reboot_evidence,
        )

        payload = build_local_gate_d_mic_diagnostics_after_reboot_evidence()
        output = _gate_d_mic_diagnostics_after_reboot_evidence_json(payload)
    except (ImportError, KeyError, RuntimeError, TypeError, ValueError):
        print(
            _GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(output)
    return 0


def _gate_d_mic_diagnostics_after_reboot_evidence_json(payload: object) -> str:
    if (
        type(payload) is not dict
        or tuple(payload) != _GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_KEYS
    ):
        raise ValueError(_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_CLI_ERROR)
    if payload["evidence_kind"] != "local_gate_d_mic_diagnostics_after_reboot_evidence":
        raise ValueError(_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_CLI_ERROR)
    for key, expected in _GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_STATUSES.items():
        if payload[key] != expected:
            raise ValueError(_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_CLI_ERROR)
    if any(
        payload[flag] is not False
        for flag in _GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_FALSE_FLAGS
    ):
        raise ValueError(_GATE_D_MIC_DIAGNOSTICS_AFTER_REBOOT_EVIDENCE_CLI_ERROR)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _run_gate_d_signal_quality_evidence_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar gate-d-signal-quality-evidence-local",
        description=(
            "Build a metadata-only local Gate D public-open signal quality "
            "evidence summary from fixed checks."
        ),
        fixed_error_message=_GATE_D_SIGNAL_QUALITY_EVIDENCE_CLI_ERROR,
    )
    args = parser.parse_args(argv)
    return _run_gate_d_signal_quality_evidence_local_command(args)


def _run_gate_d_signal_quality_evidence_local_command(
    args: argparse.Namespace,
) -> int:
    try:
        from async_scholar.gate_d_signal_quality_evidence import (
            build_local_gate_d_signal_quality_evidence,
        )

        payload = build_local_gate_d_signal_quality_evidence()
        output = _gate_d_signal_quality_evidence_json(payload)
    except (ImportError, KeyError, RuntimeError, TypeError, ValueError):
        print(_GATE_D_SIGNAL_QUALITY_EVIDENCE_CLI_ERROR, file=sys.stderr)
        return 1

    print(output)
    return 0


def _gate_d_signal_quality_evidence_json(payload: object) -> str:
    if (
        type(payload) is not dict
        or tuple(payload) != _GATE_D_SIGNAL_QUALITY_EVIDENCE_KEYS
    ):
        raise ValueError(_GATE_D_SIGNAL_QUALITY_EVIDENCE_CLI_ERROR)
    if payload["evidence_kind"] != "local_gate_d_public_open_signal_quality_evidence":
        raise ValueError(_GATE_D_SIGNAL_QUALITY_EVIDENCE_CLI_ERROR)
    for key, expected in _GATE_D_SIGNAL_QUALITY_EVIDENCE_STATUSES.items():
        if payload[key] != expected:
            raise ValueError(_GATE_D_SIGNAL_QUALITY_EVIDENCE_CLI_ERROR)
    for key, expected in _GATE_D_SIGNAL_QUALITY_EVIDENCE_SCALARS.items():
        if payload[key] != expected:
            raise ValueError(_GATE_D_SIGNAL_QUALITY_EVIDENCE_CLI_ERROR)
    if any(
        payload[flag] is not True for flag in _GATE_D_SIGNAL_QUALITY_EVIDENCE_TRUE_FLAGS
    ):
        raise ValueError(_GATE_D_SIGNAL_QUALITY_EVIDENCE_CLI_ERROR)
    if any(
        payload[flag] is not False
        for flag in _GATE_D_SIGNAL_QUALITY_EVIDENCE_FALSE_FLAGS
    ):
        raise ValueError(_GATE_D_SIGNAL_QUALITY_EVIDENCE_CLI_ERROR)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _run_gate_d_product_judgment_evidence_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar gate-d-product-judgment-evidence-local",
        description=(
            "Build a metadata-only local Gate D product-judgment evidence "
            "summary from fixed checks."
        ),
        fixed_error_message=_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_CLI_ERROR,
    )
    args = parser.parse_args(argv)
    return _run_gate_d_product_judgment_evidence_local_command(args)


def _run_gate_d_product_judgment_evidence_local_command(
    args: argparse.Namespace,
) -> int:
    try:
        from async_scholar.gate_d_product_judgment_evidence import (
            build_local_gate_d_product_judgment_evidence,
        )

        payload = build_local_gate_d_product_judgment_evidence()
        output = _gate_d_product_judgment_evidence_json(payload)
    except (ImportError, KeyError, RuntimeError, TypeError, ValueError):
        print(_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_CLI_ERROR, file=sys.stderr)
        return 1

    print(output)
    return 0


def _gate_d_product_judgment_evidence_json(payload: object) -> str:
    if (
        type(payload) is not dict
        or tuple(payload) != _GATE_D_PRODUCT_JUDGMENT_EVIDENCE_KEYS
    ):
        raise ValueError(_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_CLI_ERROR)
    if payload["evidence_kind"] != "local_gate_d_product_judgment_evidence":
        raise ValueError(_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_CLI_ERROR)
    for key, expected in _GATE_D_PRODUCT_JUDGMENT_EVIDENCE_STATUSES.items():
        if payload[key] != expected:
            raise ValueError(_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_CLI_ERROR)
    if any(
        payload[flag] is not False
        for flag in _GATE_D_PRODUCT_JUDGMENT_EVIDENCE_FALSE_FLAGS
    ):
        raise ValueError(_GATE_D_PRODUCT_JUDGMENT_EVIDENCE_CLI_ERROR)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _run_gate_d_scheduler_lifecycle_evidence_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar gate-d-scheduler-lifecycle-evidence-local",
        description=(
            "Build a metadata-only local Gate D scheduler-lifecycle evidence "
            "summary from fixed checks."
        ),
        fixed_error_message=_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_CLI_ERROR,
    )
    args = parser.parse_args(argv)
    return _run_gate_d_scheduler_lifecycle_evidence_local_command(args)


def _run_gate_d_scheduler_lifecycle_evidence_local_command(
    args: argparse.Namespace,
) -> int:
    try:
        from async_scholar.gate_d_scheduler_lifecycle_evidence import (
            build_local_gate_d_scheduler_lifecycle_evidence,
        )

        payload = build_local_gate_d_scheduler_lifecycle_evidence()
        output = _gate_d_scheduler_lifecycle_evidence_json(payload)
    except (ImportError, KeyError, RuntimeError, TypeError, ValueError):
        print(_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_CLI_ERROR, file=sys.stderr)
        return 1

    print(output)
    return 0


def _gate_d_scheduler_lifecycle_evidence_json(payload: object) -> str:
    if (
        type(payload) is not dict
        or tuple(payload) != _GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_KEYS
    ):
        raise ValueError(_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_CLI_ERROR)
    if payload["evidence_kind"] != "local_gate_d_scheduler_lifecycle_evidence":
        raise ValueError(_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_CLI_ERROR)
    for key, expected in _GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_STATUSES.items():
        if payload[key] != expected:
            raise ValueError(_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_CLI_ERROR)
    if any(
        payload[flag] is not False
        for flag in _GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_FALSE_FLAGS
    ):
        raise ValueError(_GATE_D_SCHEDULER_LIFECYCLE_EVIDENCE_CLI_ERROR)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _run_gate_d_rollback_plan_evidence_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar gate-d-rollback-plan-evidence-local",
        description=(
            "Build a metadata-only local Gate D rollback-plan evidence summary "
            "from fixed checks."
        ),
        fixed_error_message=_GATE_D_ROLLBACK_PLAN_EVIDENCE_CLI_ERROR,
    )
    args = parser.parse_args(argv)
    return _run_gate_d_rollback_plan_evidence_local_command(args)


def _run_gate_d_rollback_plan_evidence_local_command(
    args: argparse.Namespace,
) -> int:
    try:
        from async_scholar.gate_d_rollback_plan_evidence import (
            build_local_gate_d_rollback_plan_evidence,
        )

        payload = build_local_gate_d_rollback_plan_evidence()
        output = _gate_d_rollback_plan_evidence_json(payload)
    except (ImportError, KeyError, RuntimeError, TypeError, ValueError):
        print(_GATE_D_ROLLBACK_PLAN_EVIDENCE_CLI_ERROR, file=sys.stderr)
        return 1

    print(output)
    return 0


def _gate_d_rollback_plan_evidence_json(payload: object) -> str:
    if (
        type(payload) is not dict
        or tuple(payload) != _GATE_D_ROLLBACK_PLAN_EVIDENCE_KEYS
    ):
        raise ValueError(_GATE_D_ROLLBACK_PLAN_EVIDENCE_CLI_ERROR)
    if payload["evidence_kind"] != "local_gate_d_rollback_plan_evidence":
        raise ValueError(_GATE_D_ROLLBACK_PLAN_EVIDENCE_CLI_ERROR)
    for key, expected in _GATE_D_ROLLBACK_PLAN_EVIDENCE_STATUSES.items():
        if payload[key] != expected:
            raise ValueError(_GATE_D_ROLLBACK_PLAN_EVIDENCE_CLI_ERROR)
    if any(
        payload[flag] is not False
        for flag in _GATE_D_ROLLBACK_PLAN_EVIDENCE_FALSE_FLAGS
    ):
        raise ValueError(_GATE_D_ROLLBACK_PLAN_EVIDENCE_CLI_ERROR)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _run_gate_d_local_evidence_bundle_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar gate-d-local-evidence-bundle",
        description=(
            "Build a metadata-only local Gate D smoke evidence bundle from "
            "fixed synthetic checks."
        ),
        fixed_error_message=_GATE_D_LOCAL_EVIDENCE_BUNDLE_CLI_ERROR,
    )
    args = parser.parse_args(argv)
    return _run_gate_d_local_evidence_bundle_command(args)


def _run_gate_d_local_evidence_bundle_command(args: argparse.Namespace) -> int:
    try:
        from async_scholar.gate_d_local_evidence_bundle import (
            build_local_gate_d_smoke_evidence_bundle,
        )

        payload = build_local_gate_d_smoke_evidence_bundle()
        output = _gate_d_local_evidence_bundle_json(payload)
    except (ImportError, KeyError, RuntimeError, TypeError, ValueError):
        print(_GATE_D_LOCAL_EVIDENCE_BUNDLE_CLI_ERROR, file=sys.stderr)
        return 1

    print(output)
    return 0


def _gate_d_local_evidence_bundle_json(payload: object) -> str:
    if (
        type(payload) is not dict
        or tuple(payload) != _GATE_D_LOCAL_EVIDENCE_BUNDLE_KEYS
    ):
        raise ValueError(_GATE_D_LOCAL_EVIDENCE_BUNDLE_CLI_ERROR)
    if payload["bundle_kind"] != "local_gate_d_smoke_evidence_bundle":
        raise ValueError(_GATE_D_LOCAL_EVIDENCE_BUNDLE_CLI_ERROR)
    for key, expected in _GATE_D_LOCAL_EVIDENCE_BUNDLE_STATUSES.items():
        if payload[key] != expected:
            raise ValueError(_GATE_D_LOCAL_EVIDENCE_BUNDLE_CLI_ERROR)
    if (
        payload["missing_evidence"] != _GATE_D_LOCAL_EVIDENCE_BUNDLE_MISSING
        or payload["missing_evidence_count"] != 0
        or payload["blocking_evidence"] != _GATE_D_LOCAL_EVIDENCE_BUNDLE_BLOCKING
        or payload["blocking_evidence_count"] != 1
        or payload["satisfactory_evidence_count"] != 9
        or payload["readiness_decision"] != "blocked"
        or payload["readiness_reason"]
        != "required_gate_d_readiness_evidence_missing_or_blocking"
        or payload["gap_decision"] != "gaps_present"
        or payload["gap_reason"] != "required_gate_d_evidence_gaps_present"
    ):
        raise ValueError(_GATE_D_LOCAL_EVIDENCE_BUNDLE_CLI_ERROR)
    if any(
        payload[flag] is not False for flag in _GATE_D_LOCAL_EVIDENCE_BUNDLE_FALSE_FLAGS
    ):
        raise ValueError(_GATE_D_LOCAL_EVIDENCE_BUNDLE_CLI_ERROR)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _run_session_window_lifecycle_smoke_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-lifecycle-smoke-local",
        description=(
            "Run one bounded local session-window start and stop lifecycle with "
            "fixed synthetic metadata."
        ),
        fixed_error_message=_SESSION_WINDOW_LIFECYCLE_SMOKE_CLI_ERROR,
    )
    _add_session_window_lifecycle_smoke_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_lifecycle_smoke_local_command(args)


def _run_session_window_lifecycle_smoke_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_lifecycle_smoke import (
        build_local_session_window_lifecycle_smoke,
    )

    try:
        payload = build_local_session_window_lifecycle_smoke(
            args.db_path,
            args.archive_root,
            enabled=not args.disabled,
        )
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        print(_SESSION_WINDOW_LIFECYCLE_SMOKE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_scheduled_start_preview_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar scheduled-start-preview-local",
        description=(
            "Preview one non-executing scheduled-start decision from explicit "
            "local metadata and an explicit local clock."
        ),
        fixed_error_message=_SCHEDULED_START_PREVIEW_CLI_ERROR,
    )
    _add_scheduled_start_preview_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_scheduled_start_preview_local_command(args)


def _run_scheduled_start_preview_local_command(args: argparse.Namespace) -> int:
    from async_scholar.schedule_config import ScheduleConfig
    from async_scholar.scheduled_start import (
        ScheduledStartClock,
        build_scheduled_start_manual_result,
        build_scheduled_start_plan,
        scheduled_start_manual_result_safe_summary,
    )

    try:
        schedule_config = ScheduleConfig(
            course_id=args.course_id,
            class_times=[
                {
                    "day_of_week": args.day_of_week,
                    "local_start_time": args.local_start_time,
                    "duration_minutes": args.duration_minutes,
                }
            ],
        )
        plan = build_scheduled_start_plan(
            schedule_config,
            selected_class_time_index=0,
            source_kind=args.source_kind,
            enabled=not args.disabled,
        )
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        preview = build_scheduled_start_manual_result(
            plan,
            clock,
            args.session_id,
        )
        payload = scheduled_start_manual_result_safe_summary(preview)
    except ValueError:
        print(_SCHEDULED_START_PREVIEW_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_course_schedule_summary_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar course-schedule-summary-local",
        description=(
            "Summarize one stored local course schedule from an explicit "
            "read-only SQLite database path."
        ),
        fixed_error_message=_COURSE_SCHEDULE_SUMMARY_CLI_ERROR,
    )
    _add_course_schedule_summary_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_course_schedule_summary_local_command(args)


def _run_course_schedule_summary_local_command(args: argparse.Namespace) -> int:
    from async_scholar.schedule_store import (
        COURSE_SCHEDULE_SUMMARY_ERROR,
        load_course_schedule_safe_summary,
    )

    try:
        payload = load_course_schedule_safe_summary(
            args.db_path,
            args.course_id,
        )
    except ValueError:
        print(COURSE_SCHEDULE_SUMMARY_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _run_course_schedule_list_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar course-schedule-list-local",
        description=(
            "List stored local course schedule metadata from an explicit "
            "read-only SQLite database path."
        ),
        fixed_error_message=_COURSE_SCHEDULE_LIST_CLI_ERROR,
    )
    _add_course_schedule_list_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_course_schedule_list_local_command(args)


def _run_course_schedule_list_local_command(args: argparse.Namespace) -> int:
    from async_scholar.schedule_store import (
        COURSE_SCHEDULE_LIST_ERROR,
        list_course_schedule_safe_summaries,
    )

    try:
        payload = _course_schedule_list_safe_summary(
            list_course_schedule_safe_summaries(args.db_path)
        )
    except (KeyError, TypeError, ValueError):
        print(COURSE_SCHEDULE_LIST_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _course_schedule_list_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_COURSE_SCHEDULE_LIST_CLI_ERROR)
    return {
        "course_count": payload["course_count"],
        "courses": [_course_schedule_safe_summary(course) for course in courses],
    }


def _run_course_schedule_save_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar course-schedule-save-local",
        description=(
            "Save one validated local course schedule into an explicit SQLite "
            "database path without executing a scheduler."
        ),
        fixed_error_message=_COURSE_SCHEDULE_SAVE_CLI_ERROR,
    )
    _add_course_schedule_save_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_course_schedule_save_local_command(args)


def _run_course_schedule_save_local_command(args: argparse.Namespace) -> int:
    from async_scholar.course_metadata import CourseMetadata
    from async_scholar.schedule_config import ScheduleConfig
    from async_scholar.schedule_store import save_course_schedule

    try:
        course_metadata = CourseMetadata(
            course_id=args.course_id,
            title=args.title,
            instructor_name=args.instructor_name,
            meeting_url=args.meeting_url,
            meeting_label=args.meeting_label,
        )
        schedule_config = ScheduleConfig(
            course_id=args.course_id,
            class_times=[
                _parse_course_schedule_class_time(class_time)
                for class_time in args.class_time
            ],
        )
        stored_schedule = save_course_schedule(
            args.db_path,
            course_metadata,
            schedule_config,
        )
        safe_payload = _course_schedule_safe_summary(stored_schedule.safe_summary())
    except (KeyError, TypeError, ValueError):
        print(_COURSE_SCHEDULE_SAVE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(safe_payload, sort_keys=True))
    return 0


def _course_schedule_safe_summary(payload: dict[str, object]) -> dict[str, object]:
    return {key: payload[key] for key in _COURSE_SCHEDULE_SAFE_SUMMARY_KEYS}


def _parse_course_schedule_class_time(value: object) -> dict[str, object]:
    if not isinstance(value, str):
        raise ValueError(_COURSE_SCHEDULE_SAVE_CLI_ERROR)

    parts = value.split(",")
    if len(parts) < 3 or len(parts) > 5:
        raise ValueError(_COURSE_SCHEDULE_SAVE_CLI_ERROR)

    day_of_week, local_start_time, duration_text, *optional_parts = parts
    try:
        duration_minutes = int(duration_text)
    except ValueError:
        raise ValueError(_COURSE_SCHEDULE_SAVE_CLI_ERROR) from None

    class_time: dict[str, object] = {
        "day_of_week": day_of_week,
        "local_start_time": local_start_time,
        "duration_minutes": duration_minutes,
    }
    if optional_parts:
        class_time["timezone_name"] = optional_parts[0]
    if len(optional_parts) == 2:
        class_time["meeting_label"] = optional_parts[1]
    return class_time


def _run_scheduled_start_preview_from_store_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar scheduled-start-preview-from-store-local",
        description=(
            "Preview one non-executing scheduled-start decision from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
        fixed_error_message=_SCHEDULED_START_PREVIEW_FROM_STORE_CLI_ERROR,
    )
    _add_scheduled_start_preview_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_scheduled_start_preview_from_store_local_command(args)


def _run_scheduled_start_preview_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import load_course_schedule_read_only
    from async_scholar.scheduled_start import (
        ScheduledStartClock,
        build_scheduled_start_manual_result,
        build_scheduled_start_plan,
        scheduled_start_manual_result_safe_summary,
    )

    try:
        stored_schedule = load_course_schedule_read_only(
            args.db_path,
            args.course_id,
        )
        plan = build_scheduled_start_plan(
            stored_schedule.schedule_config,
            selected_class_time_index=args.class_time_index,
            source_kind=args.source_kind,
            enabled=not args.disabled,
        )
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        preview = build_scheduled_start_manual_result(
            plan,
            clock,
            args.session_id,
        )
        payload = _stored_schedule_preview_safe_summary(
            scheduled_start_manual_result_safe_summary(preview)
        )
    except (KeyError, TypeError, ValueError):
        print(_SCHEDULED_START_PREVIEW_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_schedule_preview_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {key: payload[key] for key in _STORED_SCHEDULED_START_PREVIEW_KEYS}


def _run_scheduled_start_next_from_store_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar scheduled-start-next-from-store-local",
        description=(
            "Preview the next non-executing scheduled-start decision from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
        fixed_error_message=_SCHEDULED_START_NEXT_FROM_STORE_CLI_ERROR,
    )
    _add_scheduled_start_next_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_scheduled_start_next_from_store_local_command(args)


def _run_scheduled_start_next_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import load_course_schedule_read_only
    from async_scholar.scheduled_start import (
        ScheduledStartClock,
        build_next_scheduled_start_preview_summary,
    )

    try:
        stored_schedule = load_course_schedule_read_only(
            args.db_path,
            args.course_id,
        )
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_schedule_next_preview_safe_summary(
            build_next_scheduled_start_preview_summary(
                stored_schedule.schedule_config,
                clock,
                args.session_id,
                args.source_kind,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(_SCHEDULED_START_NEXT_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_schedule_next_preview_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {key: payload[key] for key in _STORED_SCHEDULED_START_NEXT_PREVIEW_KEYS}


def _run_scheduled_start_due_list_from_store_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar scheduled-start-due-list-from-store-local",
        description=(
            "List due non-executing scheduled-start metadata from an explicit "
            "read-only local schedule store and explicit local clock."
        ),
        fixed_error_message=_SCHEDULED_START_DUE_LIST_FROM_STORE_CLI_ERROR,
    )
    _add_scheduled_start_due_list_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_scheduled_start_due_list_from_store_local_command(args)


def _run_scheduled_start_due_list_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_due_list_inputs
    from async_scholar.scheduled_start import (
        ScheduledStartClock,
        build_scheduled_start_due_list_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_schedule_due_list_safe_summary(
            build_scheduled_start_due_list_summary(
                list_course_schedule_due_list_inputs(args.db_path),
                clock,
                args.session_id,
                args.source_kind,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(_SCHEDULED_START_DUE_LIST_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_schedule_due_list_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SCHEDULED_START_DUE_LIST_FROM_STORE_CLI_ERROR)
    safe_payload = {key: payload[key] for key in _STORED_SCHEDULED_START_DUE_LIST_KEYS}
    safe_payload["courses"] = [
        _stored_schedule_due_list_course_safe_summary(course) for course in courses
    ]
    return safe_payload


def _stored_schedule_due_list_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {key: payload[key] for key in _STORED_SCHEDULED_START_DUE_LIST_COURSE_KEYS}


def _run_session_stop_preview_from_store_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-stop-preview-from-store-local",
        description=(
            "Preview one non-executing session-stop decision from an explicit "
            "read-only local schedule store."
        ),
        fixed_error_message=_SESSION_STOP_PREVIEW_FROM_STORE_CLI_ERROR,
    )
    _add_session_stop_preview_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_stop_preview_from_store_local_command(args)


def _run_session_stop_preview_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import load_course_schedule_session_stop_input
    from async_scholar.session_stop import build_session_stop_preview_from_store_input

    try:
        payload = _stored_session_stop_preview_safe_summary(
            build_session_stop_preview_from_store_input(
                load_course_schedule_session_stop_input(
                    args.db_path,
                    args.course_id,
                    args.class_time_index,
                ),
                args.source_kind,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(_SESSION_STOP_PREVIEW_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_stop_preview_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {key: payload[key] for key in _STORED_SESSION_STOP_PREVIEW_KEYS}


def _run_session_window_plan_from_store_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-plan-from-store-local",
        description=(
            "Build due non-executing session-window metadata from an explicit "
            "read-only local schedule store and explicit local clock."
        ),
        fixed_error_message=_SESSION_WINDOW_PLAN_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_plan_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_plan_from_store_local_command(args)


def _run_session_window_plan_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window import build_stored_session_window_plan_summary

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_session_window_plan_safe_summary(
            build_stored_session_window_plan_summary(
                list_course_schedule_session_window_inputs(args.db_path),
                clock,
                args.session_id,
                args.source_kind,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(_SESSION_WINDOW_PLAN_FROM_STORE_CLI_ERROR, file=sys.stderr)
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_plan_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_PLAN_FROM_STORE_CLI_ERROR)
    safe_payload = {key: payload[key] for key in _STORED_SESSION_WINDOW_PLAN_KEYS}
    safe_payload["courses"] = [
        _stored_session_window_plan_course_safe_summary(course) for course in courses
    ]
    return safe_payload


def _stored_session_window_plan_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {key: payload[key] for key in _STORED_SESSION_WINDOW_PLAN_COURSE_KEYS}


def _run_session_window_archive_preflight_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-archive-preflight-from-store-local",
        description=(
            "Build read-only session-window archive preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
        fixed_error_message=_SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_archive_preflight_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_archive_preflight_from_store_local_command(args)


def _run_session_window_archive_preflight_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_archive_preflight import (
        build_session_window_archive_preflight_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_session_window_archive_preflight_safe_summary(
            build_session_window_archive_preflight_summary(
                list_course_schedule_session_window_inputs(args.db_path),
                args.archive_root,
                args.session_id,
                args.source_kind,
                clock,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_archive_preflight_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_ARCHIVE_PREFLIGHT_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_KEYS
    }
    safe_payload["courses"] = [
        _stored_session_window_archive_preflight_course_safe_summary(course)
        for course in courses
    ]
    return safe_payload


def _stored_session_window_archive_preflight_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {
        key: payload[key]
        for key in _STORED_SESSION_WINDOW_ARCHIVE_PREFLIGHT_COURSE_KEYS
    }


def _run_session_window_alert_preview_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-alert-preview-from-store-local",
        description=(
            "Build metadata-only session-window alert preview data from an "
            "explicit read-only local schedule store and explicit local clock."
        ),
        fixed_error_message=_SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_alert_preview_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_alert_preview_from_store_local_command(args)


def _run_session_window_alert_preview_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_alert_preview import (
        build_session_window_alert_preview_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_session_window_alert_preview_safe_summary(
            build_session_window_alert_preview_summary(
                list_course_schedule_session_window_inputs(args.db_path),
                args.session_id,
                args.source_kind,
                clock,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_alert_preview_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_ALERT_PREVIEW_KEYS
    }
    safe_payload["courses"] = [
        _stored_session_window_alert_preview_course_safe_summary(course)
        for course in courses
    ]
    return safe_payload


def _stored_session_window_alert_preview_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_ALERT_PREVIEW_COURSE_KEYS
    }
    alert_preview = safe_payload["alert_preview"]
    if not isinstance(alert_preview, dict):
        raise ValueError(_SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR)
    safe_payload["alert_preview"] = {
        key: alert_preview[key]
        for key in _STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA_KEYS
    }
    if safe_payload["alert_preview"] != _STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA:
        raise ValueError(_SESSION_WINDOW_ALERT_PREVIEW_FROM_STORE_CLI_ERROR)
    return safe_payload


def _run_session_window_readiness_preflight_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-readiness-preflight-from-store-local",
        description=(
            "Build read-only session-window readiness preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
        fixed_error_message=_SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_readiness_preflight_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_readiness_preflight_from_store_local_command(args)


def _run_session_window_readiness_preflight_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_readiness_preflight import (
        build_session_window_readiness_preflight_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_session_window_readiness_preflight_safe_summary(
            build_session_window_readiness_preflight_summary(
                list_course_schedule_session_window_inputs(args.db_path),
                args.archive_root,
                args.session_id,
                args.source_kind,
                clock,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_readiness_preflight_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_READINESS_PREFLIGHT_KEYS
    }
    safe_payload["courses"] = [
        _stored_session_window_readiness_preflight_course_safe_summary(course)
        for course in courses
    ]
    return safe_payload


def _stored_session_window_readiness_preflight_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    safe_payload = {
        key: payload[key]
        for key in _STORED_SESSION_WINDOW_READINESS_PREFLIGHT_COURSE_KEYS
    }
    alert_preview = safe_payload["alert_preview"]
    if not isinstance(alert_preview, dict):
        raise ValueError(_SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR)
    safe_payload["alert_preview"] = {
        key: alert_preview[key]
        for key in _STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA_KEYS
    }
    if safe_payload["alert_preview"] != _STORED_SESSION_WINDOW_ALERT_PREVIEW_METADATA:
        raise ValueError(_SESSION_WINDOW_READINESS_PREFLIGHT_FROM_STORE_CLI_ERROR)
    return safe_payload


def _run_session_window_confirmation_preflight_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-confirmation-preflight-from-store-local",
        description=(
            "Build read-only session-window confirmation preflight metadata from an "
            "explicit read-only local schedule store, archive root, and local clock."
        ),
        fixed_error_message=_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_confirmation_preflight_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_confirmation_preflight_from_store_local_command(args)


def _run_session_window_confirmation_preflight_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_confirmation_preflight import (
        build_session_window_confirmation_preflight_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = _stored_session_window_confirmation_preflight_safe_summary(
            build_session_window_confirmation_preflight_summary(
                list_course_schedule_session_window_inputs(args.db_path),
                args.archive_root,
                args.session_id,
                args.source_kind,
                clock,
                enabled=not args.disabled,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_confirmation_preflight_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_KEYS
    }
    if safe_payload["status"] != safe_payload["confirmation_status"]:
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR)
    if (
        safe_payload["confirmation_status"]
        not in _STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_STATUSES
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR)
    safe_payload["courses"] = [
        _stored_session_window_confirmation_preflight_course_safe_summary(course)
        for course in courses
    ]
    if not safe_payload["confirmation_required"] and (
        safe_payload["blocked_execution_count"] != 0 or safe_payload["courses"]
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR)
    if safe_payload["confirmation_required"] and (
        safe_payload["blocked_execution_count"] != safe_payload["due_count"]
        or any(
            not course["requires_confirmation"] for course in safe_payload["courses"]
        )
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_FROM_STORE_CLI_ERROR)
    return safe_payload


def _stored_session_window_confirmation_preflight_course_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    return {
        key: payload[key]
        for key in _STORED_SESSION_WINDOW_CONFIRMATION_PREFLIGHT_COURSE_KEYS
    }


def _run_session_window_confirmation_response_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-confirmation-response-from-store-local",
        description=(
            "Build non-executing session-window confirmation response metadata from "
            "an explicit read-only local schedule store, archive root, local clock, "
            "and fixed confirmation response."
        ),
        fixed_error_message=_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_confirmation_response_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_confirmation_response_from_store_local_command(args)


def _run_session_window_confirmation_response_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_confirmation_preflight import (
        build_session_window_confirmation_preflight_summary,
    )
    from async_scholar.session_window_confirmation_response import (
        build_session_window_confirmation_response_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        preflight_payload = build_session_window_confirmation_preflight_summary(
            list_course_schedule_session_window_inputs(args.db_path),
            args.archive_root,
            args.session_id,
            args.source_kind,
            clock,
            enabled=not args.disabled,
        )
        payload = _stored_session_window_confirmation_response_safe_summary(
            build_session_window_confirmation_response_summary(
                preflight_payload,
                args.confirmation_response,
            )
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_confirmation_response_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_KEYS
    }
    if (
        safe_payload["status"]
        not in _STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_STATUSES
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR)
    if (
        safe_payload["confirmation_response"]
        not in _STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_TOKENS
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR)
    safe_payload["courses"] = [
        _stored_session_window_confirmation_response_course_safe_summary(
            course,
            safe_payload["confirmation_response"],
        )
        for course in courses
    ]
    if (
        safe_payload["status"] in ("disabled", "not_required")
        and safe_payload["courses"]
    ):
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR)
    return safe_payload


def _stored_session_window_confirmation_response_course_safe_summary(
    payload: dict[str, object],
    confirmation_response: object,
) -> dict[str, object]:
    safe_payload = {
        key: payload[key]
        for key in _STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_COURSE_KEYS
    }
    if safe_payload["confirmation_response"] != confirmation_response:
        raise ValueError(_SESSION_WINDOW_CONFIRMATION_RESPONSE_FROM_STORE_CLI_ERROR)
    return safe_payload


def _run_session_window_start_authorization_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-start-authorization-from-store-local",
        description=(
            "Build non-executing session-window start authorization metadata from "
            "an explicit read-only local schedule store, archive root, local clock, "
            "and fixed confirmation response."
        ),
        fixed_error_message=_SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_start_authorization_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_start_authorization_from_store_local_command(args)


def _run_session_window_start_authorization_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_confirmation_preflight import (
        build_session_window_confirmation_preflight_summary,
    )
    from async_scholar.session_window_confirmation_response import (
        build_session_window_confirmation_response_summary,
    )
    from async_scholar.session_window_start_authorization import (
        build_session_window_start_authorization_summary,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        preflight_payload = build_session_window_confirmation_preflight_summary(
            list_course_schedule_session_window_inputs(args.db_path),
            args.archive_root,
            args.session_id,
            args.source_kind,
            clock,
            enabled=not args.disabled,
        )
        response_payload = build_session_window_confirmation_response_summary(
            preflight_payload,
            args.confirmation_response,
        )
        payload = _stored_session_window_start_authorization_safe_summary(
            build_session_window_start_authorization_summary(response_payload)
        )
    except (KeyError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True))
    return 0


def _stored_session_window_start_authorization_safe_summary(
    payload: dict[str, object],
) -> dict[str, object]:
    courses = payload["courses"]
    if not isinstance(courses, list):
        raise ValueError(_SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR)
    safe_payload = {
        key: payload[key] for key in _STORED_SESSION_WINDOW_START_AUTHORIZATION_KEYS
    }
    if (
        safe_payload["status"]
        not in _STORED_SESSION_WINDOW_START_AUTHORIZATION_STATUSES
    ):
        raise ValueError(_SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR)
    if (
        safe_payload["confirmation_response"]
        not in _STORED_SESSION_WINDOW_CONFIRMATION_RESPONSE_TOKENS
    ):
        raise ValueError(_SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR)
    if (
        safe_payload["block_reason"]
        not in _STORED_SESSION_WINDOW_START_AUTHORIZATION_BLOCK_REASONS
    ):
        raise ValueError(_SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR)
    safe_payload["courses"] = [
        _stored_session_window_start_authorization_course_safe_summary(
            course,
            safe_payload["confirmation_response"],
        )
        for course in courses
    ]
    if safe_payload["authorized"] and (
        safe_payload["status"] != "authorized"
        or safe_payload["block_reason"] != "none"
        or safe_payload["blocked_start_count"] != 0
        or safe_payload["authorized_start_count"] != safe_payload["due_count"]
        or any(not course["authorized"] for course in safe_payload["courses"])
    ):
        raise ValueError(_SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR)
    if not safe_payload["authorized"] and safe_payload["courses"]:
        raise ValueError(_SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR)
    return safe_payload


def _stored_session_window_start_authorization_course_safe_summary(
    payload: dict[str, object],
    confirmation_response: object,
) -> dict[str, object]:
    safe_payload = {
        key: payload[key]
        for key in _STORED_SESSION_WINDOW_START_AUTHORIZATION_COURSE_KEYS
    }
    if safe_payload["confirmation_response"] != confirmation_response:
        raise ValueError(_SESSION_WINDOW_START_AUTHORIZATION_FROM_STORE_CLI_ERROR)
    return safe_payload


def _run_session_window_execution_preflight_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-execution-preflight-from-store-local",
        description=(
            "Build read-only one-shot session-window execution preflight metadata "
            "from an explicit read-only local schedule store, archive root, local "
            "clock, and same-invocation fixed confirmation response."
        ),
        fixed_error_message=_SESSION_WINDOW_EXECUTION_PREFLIGHT_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_execution_preflight_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_execution_preflight_from_store_local_command(args)


def _run_session_window_execution_preflight_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_execution_preflight import (
        build_stored_session_window_execution_preflight_from_store,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = build_stored_session_window_execution_preflight_from_store(
            args.db_path,
            args.archive_root,
            args.session_id,
            args.source_kind,
            clock,
            args.confirmation_response,
            enabled=not args.disabled,
        )
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_EXECUTION_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_execute_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-execute-from-store-local",
        description=(
            "Run one-shot stored session-window execution metadata from an "
            "explicit local schedule store, archive root, local clock, and "
            "same-invocation fixed confirmation response."
        ),
        fixed_error_message=_SESSION_WINDOW_EXECUTION_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_execute_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_execute_from_store_local_command(args)


def _run_session_window_execute_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_execution import (
        build_stored_session_window_execution_from_store,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        payload = build_stored_session_window_execution_from_store(
            args.db_path,
            args.archive_root,
            args.session_id,
            args.source_kind,
            clock,
            args.confirmation_response,
            enabled=not args.disabled,
        )
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_EXECUTION_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_start_receipt_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-start-receipt-from-store-local",
        description=(
            "Record metadata-only session-window start receipt data from an "
            "explicit read-only local schedule store, archive root, local clock, "
            "and fixed confirmation response."
        ),
        fixed_error_message=_SESSION_WINDOW_START_RECEIPT_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_start_receipt_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_start_receipt_from_store_local_command(args)


def _run_session_window_start_receipt_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import list_course_schedule_session_window_inputs
    from async_scholar.scheduled_start import ScheduledStartClock
    from async_scholar.session_window_confirmation_preflight import (
        build_session_window_confirmation_preflight_summary,
    )
    from async_scholar.session_window_confirmation_response import (
        build_session_window_confirmation_response_summary,
    )
    from async_scholar.session_window_start_authorization import (
        build_session_window_start_authorization_summary,
    )
    from async_scholar.session_window_start_receipt import (
        write_stored_session_window_start_receipt,
    )

    try:
        clock = ScheduledStartClock(
            day_of_week=args.clock_day_of_week,
            local_time=args.clock_local_time,
        )
        preflight_payload = build_session_window_confirmation_preflight_summary(
            list_course_schedule_session_window_inputs(args.db_path),
            args.archive_root,
            args.session_id,
            args.source_kind,
            clock,
            enabled=not args.disabled,
        )
        response_payload = build_session_window_confirmation_response_summary(
            preflight_payload,
            args.confirmation_response,
        )
        authorization_payload = build_session_window_start_authorization_summary(
            response_payload
        )
        payload = write_stored_session_window_start_receipt(
            authorization_payload,
            args.archive_root,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_START_RECEIPT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_stop_receipt_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-stop-receipt-from-store-local",
        description=(
            "Record metadata-only session-window stop receipt data from an "
            "explicit read-only local schedule store and existing runtime file."
        ),
        fixed_error_message=_SESSION_WINDOW_STOP_RECEIPT_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_stop_receipt_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_stop_receipt_from_store_local_command(args)


def _run_session_window_stop_receipt_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.schedule_store import load_course_schedule_session_stop_input
    from async_scholar.session_stop import build_session_stop_preview_from_store_input
    from async_scholar.session_window_stop_receipt import (
        write_stored_session_window_stop_receipt,
    )

    try:
        stop_preview_payload = build_session_stop_preview_from_store_input(
            load_course_schedule_session_stop_input(
                args.db_path,
                args.course_id,
                args.class_time_index,
            ),
            args.source_kind,
            enabled=not args.disabled,
        )
        payload = write_stored_session_window_stop_receipt(
            stop_preview_payload,
            args.archive_root,
            args.session_id,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_STOP_RECEIPT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_stop_execution_preflight_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-stop-execution-preflight-from-store-local",
        description=(
            "Build read-only stored session-window stop execution preflight "
            "metadata from an explicit read-only local schedule store, archive "
            "root, stored class time, and source kind."
        ),
        fixed_error_message=(
            _SESSION_WINDOW_STOP_EXECUTION_PREFLIGHT_FROM_STORE_CLI_ERROR
        ),
    )
    _add_session_window_stop_execution_preflight_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_stop_execution_preflight_from_store_local_command(args)


def _run_session_window_stop_execution_preflight_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_stop_execution_preflight import (
        build_stored_session_window_stop_execution_preflight_from_store,
    )

    try:
        payload = build_stored_session_window_stop_execution_preflight_from_store(
            args.db_path,
            args.archive_root,
            args.session_id,
            args.course_id,
            args.class_time_index,
            args.source_kind,
            enabled=not args.disabled,
        )
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_STOP_EXECUTION_PREFLIGHT_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_stop_execute_from_store_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-stop-execute-from-store-local",
        description=(
            "Run one-shot stored session-window stop execution metadata from "
            "an explicit local schedule store, archive root, stored class "
            "time, source kind, and fixed confirmation response."
        ),
        fixed_error_message=_SESSION_WINDOW_STOP_EXECUTION_FROM_STORE_CLI_ERROR,
    )
    _add_session_window_stop_execute_from_store_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_stop_execute_from_store_local_command(args)


def _run_session_window_stop_execute_from_store_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_stop_execution import (
        build_stored_session_window_stop_execution_from_store,
    )

    try:
        payload = build_stored_session_window_stop_execution_from_store(
            args.db_path,
            args.archive_root,
            args.session_id,
            args.course_id,
            args.class_time_index,
            args.source_kind,
            args.confirmation_response,
            enabled=not args.disabled,
        )
    except (KeyError, OSError, RuntimeError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_STOP_EXECUTION_FROM_STORE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_runtime_summary_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-runtime-summary-local",
        description=(
            "Build a read-only metadata summary from an existing stored "
            "session-window runtime file."
        ),
        fixed_error_message=_SESSION_WINDOW_RUNTIME_SUMMARY_CLI_ERROR,
    )
    _add_session_window_runtime_summary_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_runtime_summary_local_command(args)


def _run_session_window_runtime_summary_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_runtime_summary import (
        build_stored_session_window_runtime_summary,
    )

    try:
        payload = build_stored_session_window_runtime_summary(
            args.archive_root,
            args.session_id,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RUNTIME_SUMMARY_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_recovery_decision_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-recovery-decision-local",
        description=(
            "Build a read-only stored session-window recovery decision from "
            "existing runtime and archive metadata."
        ),
        fixed_error_message=_SESSION_WINDOW_RECOVERY_DECISION_CLI_ERROR,
    )
    _add_session_window_recovery_decision_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_recovery_decision_local_command(args)


def _run_session_window_recovery_decision_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_recovery_decision import (
        build_stored_session_window_recovery_decision,
    )

    try:
        payload = build_stored_session_window_recovery_decision(
            args.archive_root,
            args.session_id,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RECOVERY_DECISION_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_recovery_review_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-recovery-review-local",
        description=(
            "Build a read-only stored session-window recovery review from "
            "existing recovery decision metadata."
        ),
        fixed_error_message=_SESSION_WINDOW_RECOVERY_REVIEW_CLI_ERROR,
    )
    _add_session_window_recovery_review_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_recovery_review_local_command(args)


def _run_session_window_recovery_review_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_recovery_review import (
        build_stored_session_window_recovery_review,
    )

    try:
        payload = build_stored_session_window_recovery_review(
            args.archive_root,
            args.session_id,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RECOVERY_REVIEW_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_recovery_review_batch_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-recovery-review-batch-local",
        description=(
            "Build a read-only stored session-window recovery review batch from "
            "explicit session identifiers."
        ),
        fixed_error_message=_SESSION_WINDOW_RECOVERY_REVIEW_BATCH_CLI_ERROR,
    )
    _add_session_window_recovery_review_batch_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_recovery_review_batch_local_command(args)


def _run_session_window_recovery_review_batch_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_recovery_batch_review import (
        build_stored_session_window_recovery_review_batch,
    )

    try:
        payload = build_stored_session_window_recovery_review_batch(
            args.archive_root,
            args.session_ids,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RECOVERY_REVIEW_BATCH_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_recovery_report_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-recovery-report-local",
        description=(
            "Build a read-only stored session-window recovery report from "
            "explicit session identifiers."
        ),
        fixed_error_message=_SESSION_WINDOW_RECOVERY_REPORT_CLI_ERROR,
    )
    _add_session_window_recovery_report_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_recovery_report_local_command(args)


def _run_session_window_recovery_report_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_recovery_report import (
        build_stored_session_window_recovery_report,
    )

    try:
        report = build_stored_session_window_recovery_report(
            args.archive_root,
            args.session_ids,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(report, end="")
    return 0


def _run_session_window_recovery_report_write_local_argv(argv: list[str]) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-recovery-report-write-local",
        description=(
            "Write a stored session-window recovery report file from explicit "
            "session identifiers."
        ),
        fixed_error_message=_SESSION_WINDOW_RECOVERY_REPORT_FILE_CLI_ERROR,
    )
    _add_session_window_recovery_report_write_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_recovery_report_write_local_command(args)


def _run_session_window_recovery_report_write_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_recovery_report_file import (
        write_stored_session_window_recovery_report_file,
    )

    try:
        payload = write_stored_session_window_recovery_report_file(
            args.archive_root,
            args.output_root,
            args.session_ids,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_recovery_report_file_inventory_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-recovery-report-file-inventory-local",
        description=(
            "Inventory the fixed stored session-window recovery report file "
            "using local metadata only."
        ),
        fixed_error_message=_SESSION_WINDOW_RECOVERY_REPORT_FILE_INVENTORY_CLI_ERROR,
    )
    _add_session_window_recovery_report_file_inventory_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_recovery_report_file_inventory_local_command(args)


def _run_session_window_recovery_report_file_inventory_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_recovery_report_file_inventory import (
        build_stored_session_window_recovery_report_file_inventory,
    )

    try:
        payload = build_stored_session_window_recovery_report_file_inventory(
            args.archive_root,
            args.output_root,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_INVENTORY_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_recovery_report_file_verification_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-recovery-report-file-verify-local",
        description=(
            "Verify the fixed stored session-window recovery report file "
            "against deterministic metadata for explicit session identifiers."
        ),
        fixed_error_message=_SESSION_WINDOW_RECOVERY_REPORT_FILE_VERIFICATION_CLI_ERROR,
    )
    _add_session_window_recovery_report_file_verification_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_recovery_report_file_verification_local_command(args)


def _run_session_window_recovery_report_file_verification_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_recovery_report_file_verification import (
        build_stored_session_window_recovery_report_file_verification,
    )

    try:
        payload = build_stored_session_window_recovery_report_file_verification(
            args.session_ids,
            args.archive_root,
            args.output_root,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_VERIFICATION_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_recovery_report_file_action_preview_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-recovery-report-file-action-preview-local",
        description=(
            "Preview the next safe local action for the fixed stored "
            "session-window recovery report file from verification metadata."
        ),
        fixed_error_message=_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_PREVIEW_CLI_ERROR,
    )
    _add_session_window_recovery_report_file_action_preview_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_recovery_report_file_action_preview_local_command(args)


def _run_session_window_recovery_report_file_action_preview_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_recovery_report_file_action_preview import (
        build_stored_session_window_recovery_report_file_action_preview,
    )

    try:
        payload = build_stored_session_window_recovery_report_file_action_preview(
            args.session_ids,
            args.archive_root,
            args.output_root,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_PREVIEW_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_recovery_report_file_action_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-recovery-report-file-action-local",
        description=(
            "Apply the next safe local action for the fixed stored "
            "session-window recovery report file."
        ),
        fixed_error_message=_SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_CLI_ERROR,
    )
    _add_session_window_recovery_report_file_action_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_recovery_report_file_action_local_command(args)


def _run_session_window_recovery_report_file_action_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_recovery_report_file_action import (
        build_stored_session_window_recovery_report_file_action,
    )

    try:
        payload = build_stored_session_window_recovery_report_file_action(
            args.session_ids,
            args.archive_root,
            args.output_root,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_ACTION_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_session_window_recovery_report_file_status_local_argv(
    argv: list[str],
) -> int:
    parser = _FixedMessageArgumentParser(
        prog="async_scholar session-window-recovery-report-file-status-local",
        description=(
            "Summarize the fixed stored session-window recovery report file "
            "status from verification metadata."
        ),
        fixed_error_message=_SESSION_WINDOW_RECOVERY_REPORT_FILE_STATUS_CLI_ERROR,
    )
    _add_session_window_recovery_report_file_status_local_arguments(parser)
    args = parser.parse_args(argv)
    return _run_session_window_recovery_report_file_status_local_command(args)


def _run_session_window_recovery_report_file_status_local_command(
    args: argparse.Namespace,
) -> int:
    from async_scholar.session_window_recovery_report_file_status import (
        build_stored_session_window_recovery_report_file_status,
    )

    try:
        payload = build_stored_session_window_recovery_report_file_status(
            args.session_ids,
            args.archive_root,
            args.output_root,
        )
    except (KeyError, OSError, TypeError, ValueError):
        print(
            _SESSION_WINDOW_RECOVERY_REPORT_FILE_STATUS_CLI_ERROR,
            file=sys.stderr,
        )
        return 1

    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


def _run_mic_recording_diagnostic_command(argv: list[str]) -> int:
    from async_scholar.audio.mic_recording_diagnostic import (
        main as run_mic_recording_diagnostic,
    )

    return run_mic_recording_diagnostic(argv)


if __name__ == "__main__":
    raise SystemExit(main())
