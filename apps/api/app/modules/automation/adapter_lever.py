"""Lever application form adapter."""
from app.modules.automation.engine import ApprovalCheckpoint, AutomationTask, SiteAdapter


class LeverSiteAdapter(SiteAdapter):
    name = "lever"

    async def fill(self, page, task: AutomationTask) -> ApprovalCheckpoint:
        answers = task.answers
        files = task.files

        # Lever renders an iframe-free apply form at /apply
        # Standard fields
        await self._fill_if_present(page, "input[name='name']", answers.get("full_name", ""))
        await self._fill_if_present(page, "input[name='email']", answers.get("email", ""))
        await self._fill_if_present(page, "input[name='phone']", answers.get("phone", ""))
        await self._fill_if_present(page, "input[name='location']", answers.get("location", ""))
        await self._fill_if_present(page, "input[name='org']", answers.get("current_company", ""))
        await self._fill_if_present(page, "input[name='urls[LinkedIn]']", answers.get("linkedin_profile", ""))
        await self._fill_if_present(page, "input[name='urls[GitHub]']", answers.get("github", ""))

        # Resume upload
        resume_path = files.get("resume")
        if resume_path:
            upload = page.locator("input[type='file'][name='resume']").first
            if await upload.count():
                await upload.set_input_files(resume_path)

        # Cover letter text area (Lever usually has a textarea)
        cover_text = answers.get("cover_letter")
        if cover_text:
            await self._fill_if_present(page, "textarea[name='comments']", cover_text)

        # Custom questions — Lever uses input[name="cards[*][field*]"]
        card_inputs = page.locator("input[name^='cards'], textarea[name^='cards']")
        count = await card_inputs.count()
        for i in range(count):
            field = card_inputs.nth(i)
            placeholder = await field.get_attribute("placeholder") or ""
            name_attr = await field.get_attribute("name") or ""
            key = placeholder.strip() or name_attr
            val = answers.get(key)
            if val:
                await field.fill(val)

        screenshot_path = f"/tmp/autoapply-{task.application_id}.png"
        await page.screenshot(path=screenshot_path, full_page=True)

        return ApprovalCheckpoint(
            summary={"fields_filled": list(answers.keys()), "files": list(files.keys()), "site": self.name},
            screenshot_path=screenshot_path,
            submit_selector="button[type='submit'], button.template-btn-submit",
        )

    @staticmethod
    async def _fill_if_present(page, selector: str, value: str) -> None:
        if not value:
            return
        locator = page.locator(selector).first
        if await locator.count():
            await locator.fill(value)
