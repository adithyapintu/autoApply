from app.modules.automation.engine import AutomationStatus


def test_automation_has_awaiting_approval_status() -> None:
    assert AutomationStatus.AWAITING_APPROVAL == "awaiting_approval"

