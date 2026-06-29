"""Workday application form adapter (multi-step wizard)."""
from app.modules.automation.engine import ApprovalCheckpoint, AutomationTask, SiteAdapter


class WorkdaySiteAdapter(SiteAdapter):
    name = "workday"

    async def fill(self, page, task: AutomationTask) -> ApprovalCheckpoint:
        answers = task.answers
        files = task.files

        # Workday uses a multi-step wizard. We fill what we can on each visible step
        # and advance if there's a "Next" button. Stop at CAPTCHA or login walls.
        MAX_STEPS = 6

        for step in range(MAX_STEPS):
            # Check for CAPTCHA — halt if detected
            captcha = page.locator("iframe[src*='recaptcha'], [class*='captcha']")
            if await captcha.count():
                break  # Safety: never bypass CAPTCHA

            # Check for authentication wall
            login_wall = page.locator("input[type='password']")
            if await login_wall.count():
                break  # Workday requires sign-in — user must handle this

            # Fill text inputs using aria-labels and placeholders
            inputs = page.locator("input[type='text'], input[type='email'], input[type='tel'], textarea")
            count = await inputs.count()
            for i in range(count):
                field = inputs.nth(i)
                aria_label = (await field.get_attribute("aria-label") or "").strip().lower()
                placeholder = (await field.get_attribute("placeholder") or "").strip().lower()
                data_automation = (await field.get_attribute("data-automation-id") or "").strip().lower()
                key = aria_label or placeholder or data_automation

                for answer_key, value in answers.items():
                    if value and answer_key.lower() in key:
                        await field.fill(value)
                        break

            # Resume upload
            if step == 0:
                resume_path = files.get("resume")
                if resume_path:
                    file_input = page.locator("input[type='file']").first
                    if await file_input.count():
                        await file_input.set_input_files(resume_path)

            # Try "Next" or "Save and Continue" button
            next_btn = page.locator(
                "button[data-automation-id='bottom-navigation-next-button'], "
                "button:has-text('Next'), button:has-text('Save and Continue')"
            ).first
            if await next_btn.count() and await next_btn.is_enabled():
                await next_btn.click()
                await page.wait_for_load_state("networkidle", timeout=8000)
            else:
                break  # No more steps or reached review page

        screenshot_path = f"/tmp/autoapply-{task.application_id}.png"
        await page.screenshot(path=screenshot_path, full_page=True)

        return ApprovalCheckpoint(
            summary={
                "fields_filled": [k for k, v in answers.items() if v],
                "files": list(files.keys()),
                "site": self.name,
                "note": "Multi-step wizard filled. Stops before CAPTCHA and auth walls.",
            },
            screenshot_path=screenshot_path,
            submit_selector=(
                "button[data-automation-id='bottom-navigation-next-button'], "
                "button:has-text('Submit'), button:has-text('Apply')"
            ),
        )
