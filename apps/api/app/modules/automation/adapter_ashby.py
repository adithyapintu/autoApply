"""Ashby application form adapter."""
from app.modules.automation.engine import ApprovalCheckpoint, AutomationTask, SiteAdapter


class AshbySiteAdapter(SiteAdapter):
    name = "ashby"

    async def fill(self, page, task: AutomationTask) -> ApprovalCheckpoint:
        answers = task.answers
        files = task.files

        # Ashby uses data-testid attributes on form fields
        test_id_map = {
            "name": answers.get("full_name") or f"{answers.get('first_name','')} {answers.get('last_name','')}".strip(),
            "email": answers.get("email", ""),
            "phone": answers.get("phone", ""),
            "linkedin": answers.get("linkedin_profile", ""),
            "github": answers.get("github", ""),
            "website": answers.get("website", ""),
        }
        for test_id, value in test_id_map.items():
            if value:
                locator = page.locator(f"[data-testid='{test_id}'] input, input[data-testid='{test_id}']").first
                if await locator.count():
                    await locator.fill(value)

        # Also try standard label-based fill
        for label_text, value in answers.items():
            if not value:
                continue
            label = page.get_by_label(label_text, exact=False)
            if await label.count():
                await label.first.fill(value)

        # Resume upload
        resume_path = files.get("resume")
        if resume_path:
            upload = page.locator("input[type='file']").first
            if await upload.count():
                await upload.set_input_files(resume_path)

        # Cover letter textarea
        cover = answers.get("cover_letter")
        if cover:
            cl_area = page.locator("textarea[name*='cover'], textarea[placeholder*='cover']").first
            if await cl_area.count():
                await cl_area.fill(cover)

        screenshot_path = f"/tmp/autoapply-{task.application_id}.png"
        await page.screenshot(path=screenshot_path, full_page=True)

        return ApprovalCheckpoint(
            summary={"fields_filled": [k for k, v in answers.items() if v], "files": list(files.keys()), "site": self.name},
            screenshot_path=screenshot_path,
            submit_selector="button[type='submit'], [data-testid='submit-application']",
        )
