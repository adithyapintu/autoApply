from dataclasses import dataclass, field
from enum import StrEnum

from playwright.async_api import async_playwright


class AutomationStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    SUBMITTED = "submitted"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AutomationTask:
    application_id: str
    target_url: str
    site_adapter: str
    answers: dict[str, str] = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)


@dataclass
class ApprovalCheckpoint:
    summary: dict
    screenshot_path: str | None
    submit_selector: str


class SiteAdapter:
    name = "generic"

    async def fill(self, page, task: AutomationTask) -> ApprovalCheckpoint:
        raise NotImplementedError


class GenericFormAdapter(SiteAdapter):
    name = "generic"

    async def fill(self, page, task: AutomationTask) -> ApprovalCheckpoint:
        for label, value in task.answers.items():
            locator = page.get_by_label(label)
            if await locator.count():
                await locator.first.fill(value)
        screenshot_path = f"/tmp/autoapply-{task.application_id}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        return ApprovalCheckpoint(
            summary={"fields_prepared": list(task.answers.keys()), "files_prepared": list(task.files.keys())},
            screenshot_path=screenshot_path,
            submit_selector="button[type=submit]",
        )


class BrowserAutomationEngine:
    def __init__(self, adapters: dict[str, SiteAdapter] | None = None):
        self.adapters = adapters or {"generic": GenericFormAdapter()}

    async def prepare_until_approval(self, task: AutomationTask) -> ApprovalCheckpoint:
        adapter = self.adapters.get(task.site_adapter, self.adapters["generic"])
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(task.target_url, wait_until="domcontentloaded")
            checkpoint = await adapter.fill(page, task)
            await browser.close()
            return checkpoint

    async def submit_after_approval(self, task: AutomationTask, checkpoint: ApprovalCheckpoint) -> dict[str, str]:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(task.target_url, wait_until="domcontentloaded")
            await page.locator(checkpoint.submit_selector).click()
            await browser.close()
        return {"status": AutomationStatus.SUBMITTED}

