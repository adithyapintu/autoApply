"""Greenhouse application form adapter."""
from app.modules.automation.engine import ApprovalCheckpoint, AutomationTask, SiteAdapter


class GreenhouseSiteAdapter(SiteAdapter):
    name = "greenhouse"

    async def fill(self, page, task: AutomationTask) -> ApprovalCheckpoint:
        answers = task.answers
        files = task.files

        # --- Resume upload ---
        resume_path = files.get("resume")
        if resume_path:
            resume_input = page.locator("input[type='file'][id*='resume'], input[type='file'][name*='resume']").first
            if await resume_input.count():
                await resume_input.set_input_files(resume_path)

        # --- Cover letter upload ---
        cover_path = files.get("cover_letter")
        if cover_path:
            cover_input = page.locator("input[type='file'][id*='cover'], input[type='file'][name*='cover']").first
            if await cover_input.count():
                await cover_input.set_input_files(cover_path)

        # --- Standard personal fields ---
        field_map = {
            "first_name": "input#first_name, input[name='first_name']",
            "last_name": "input#last_name, input[name='last_name']",
            "email": "input#email, input[name='email']",
            "phone": "input#phone, input[name='phone']",
            "location": "input#location, input[name='location']",
            "linkedin_profile": "input#job_application_answers_attributes_*[name*='linkedin']",
            "website": "input[name*='website'], input[id*='website']",
        }
        for key, selector in field_map.items():
            value = answers.get(key)
            if value:
                locator = page.locator(selector).first
                if await locator.count():
                    await locator.fill(value)

        # --- Custom questions (text inputs and textareas) ---
        custom_labels = page.locator("label.application-label")
        count = await custom_labels.count()
        for i in range(count):
            label = custom_labels.nth(i)
            label_text = (await label.inner_text()).strip()
            answer = answers.get(label_text) or answers.get(label_text.lower())
            if answer:
                for_ = await label.get_attribute("for")
                if for_:
                    field = page.locator(f"#{for_}")
                    if await field.count():
                        tag = await field.evaluate("el => el.tagName.toLowerCase()")
                        if tag in ("input", "textarea"):
                            await field.fill(answer)
                        elif tag == "select":
                            await field.select_option(label=answer)

        # --- EEO / demographic checkboxes (acknowledge only, don't modify choices) ---
        eeo_section = page.locator("[id*='eeo'], [class*='demographic']")
        if await eeo_section.count():
            decline = eeo_section.locator("option:has-text('Decline'), option:has-text('prefer not to say')")
            if await decline.count():
                pass  # leave EEO fields at their default; user can review in approval

        screenshot_path = f"/tmp/autoapply-{task.application_id}.png"
        await page.screenshot(path=screenshot_path, full_page=True)

        filled_fields = [k for k in answers if answers[k]]
        return ApprovalCheckpoint(
            summary={"fields_filled": filled_fields, "files": list(files.keys()), "site": self.name},
            screenshot_path=screenshot_path,
            submit_selector="button#submit_app, button[type='submit']",
        )
