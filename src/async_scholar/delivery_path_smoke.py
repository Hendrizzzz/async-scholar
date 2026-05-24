"""Synthetic local delivery path smoke summary."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Literal, TypedDict

from async_scholar.desktop_notifier import dispatch_desktop_notification
from async_scholar.telegram_notifier import dispatch_telegram_alert_notification

DELIVERY_PATH_SMOKE_ERROR = "delivery path smoke could not be built"
_FIXED_EVENT_TYPE = "attendance_prompt"
_FIXED_BOT_TOKEN_PLACEHOLDER = "000000:LOCAL_DELIVERY_PATH_PLACEHOLDER"
_FIXED_CHAT_ID_PLACEHOLDER = "LOCAL_DELIVERY_PATH_PLACEHOLDER"

DeliveryPathEvidenceStatus = Literal["satisfactory"]
DeliveryPathStatus = Literal["sent"]


class LocalDeliveryPathSmokeResult(TypedDict):
    delivery_path_evidence_status: DeliveryPathEvidenceStatus
    desktop_path_status: DeliveryPathStatus
    gate_d_pass_claimed: bool
    live_delivery_performed: bool
    network_performed: bool
    product_promise_alpha_pass_claimed: bool
    smoke_kind: str
    subprocess_performed: bool
    telegram_path_status: DeliveryPathStatus


class _FakeTelegramResponse:
    status = 200

    def close(self) -> None:
        return None


def build_local_delivery_path_smoke() -> LocalDeliveryPathSmokeResult:
    """Build fixed local delivery evidence without live delivery."""

    boundary_evidence = {
        "desktop_runner_called": False,
        "telegram_opener_called": False,
    }

    def fake_runner(
        _command: list[str],
        *,
        shell: bool,
        timeout: float,
    ) -> SimpleNamespace:
        if shell is not False or timeout <= 0:
            raise ValueError(DELIVERY_PATH_SMOKE_ERROR)
        boundary_evidence["desktop_runner_called"] = True
        return SimpleNamespace(returncode=0)

    def fake_opener(_request: Any, *, timeout: float | None = None) -> object:
        if timeout is not None and timeout <= 0:
            raise ValueError(DELIVERY_PATH_SMOKE_ERROR)
        boundary_evidence["telegram_opener_called"] = True
        return _FakeTelegramResponse()

    try:
        desktop_result = dispatch_desktop_notification(
            _FIXED_EVENT_TYPE,
            command_runner=fake_runner,
            platform_name="win32",
        )
        telegram_result = dispatch_telegram_alert_notification(
            _FIXED_EVENT_TYPE,
            opener=fake_opener,
            bot_token=_FIXED_BOT_TOKEN_PLACEHOLDER,
            chat_id=_FIXED_CHAT_ID_PLACEHOLDER,
        )

        desktop_status = desktop_result.status
        telegram_status = telegram_result["status"]
        if (
            desktop_status != "sent"
            or telegram_status != "sent"
            or boundary_evidence["desktop_runner_called"] is not True
            or boundary_evidence["telegram_opener_called"] is not True
        ):
            raise ValueError(DELIVERY_PATH_SMOKE_ERROR)

        return {
            "delivery_path_evidence_status": "satisfactory",
            "desktop_path_status": "sent",
            "gate_d_pass_claimed": False,
            "live_delivery_performed": False,
            "network_performed": False,
            "product_promise_alpha_pass_claimed": False,
            "smoke_kind": "local_delivery_path",
            "subprocess_performed": False,
            "telegram_path_status": "sent",
        }
    except (KeyError, RuntimeError, TypeError, ValueError):
        raise ValueError(DELIVERY_PATH_SMOKE_ERROR) from None


__all__ = [
    "DELIVERY_PATH_SMOKE_ERROR",
    "LocalDeliveryPathSmokeResult",
    "build_local_delivery_path_smoke",
]
