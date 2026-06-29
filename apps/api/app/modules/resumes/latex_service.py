import re
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

import jinja2

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_LATEX_SPECIAL = str.maketrans(
    {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
        "\\": r"\textbackslash{}",
    }
)


def _esc(value: object) -> str:
    """Escape a value for safe inclusion in a LaTeX document."""
    if value is None:
        return ""
    return str(value).translate(_LATEX_SPECIAL)


def _build_jinja_env() -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(_TEMPLATES_DIR)),
        block_start_string="((*",
        block_end_string="*))",
        variable_start_string="(((",
        variable_end_string=")))",
        comment_start_string="((#",
        comment_end_string="#))",
        trim_blocks=True,
        lstrip_blocks=True,
        autoescape=False,
    )
    env.filters["e"] = _esc
    env.filters["join"] = lambda items, sep=", ": sep.join(_esc(i) for i in items)
    return env


_env = _build_jinja_env()


def _group_skills(
    skills: list[dict], tech_stacks: list[str]
) -> dict[str, list[str]]:
    """Group skills by category, placing tech_stack-selected skills first."""
    selected = {s.lower() for s in tech_stacks}
    groups: dict[str, list[str]] = defaultdict(list)
    priority: dict[str, list[str]] = defaultdict(list)

    for skill in skills:
        name = skill.get("name", "")
        category = skill.get("category", "Other")
        if name.lower() in selected:
            priority[category].append(name)
        else:
            groups[category].append(name)

    merged: dict[str, list[str]] = {}
    all_cats = list(priority.keys()) + [c for c in groups if c not in priority]
    for cat in all_cats:
        merged[cat] = priority.get(cat, []) + groups.get(cat, [])
    return merged


def build_context(profile: dict, tech_stacks: list[str] | None = None) -> dict:
    """Convert a flat profile dict into template context."""
    ts = tech_stacks or profile.get("tech_stacks", [])

    # personal info
    personal_raw = profile.get("personal_information", {})
    personal = {k: _esc(v) for k, v in personal_raw.items()}
    if not personal.get("name"):
        personal["name"] = _esc(profile.get("full_name", ""))

    # skills — prioritise selected tech stacks
    raw_skills: list[dict] = profile.get("skills", [])
    skills_by_category = {
        _esc(cat): [_esc(s) for s in items]
        for cat, items in _group_skills(raw_skills, ts).items()
    }

    # experience — most relevant first if tech stack selected
    selected_lower = {s.lower() for s in ts}
    experience = profile.get("experience", [])
    if selected_lower:
        def _relevance(exp: dict) -> int:
            text = " ".join(
                [exp.get("description", "")]
                + exp.get("achievements", [])
                + [exp.get("title", "")]
            ).lower()
            return sum(1 for s in selected_lower if s in text)
        experience = sorted(experience, key=_relevance, reverse=True)

    def _clean_exp(e: dict) -> dict:
        return {
            "title": _esc(e.get("title", "")),
            "company": _esc(e.get("company", "")),
            "location": _esc(e.get("location", "")),
            "start_date": _esc(e.get("start_date", "")),
            "end_date": _esc(e.get("end_date", "")),
            "description": _esc(e.get("description", "")),
            "achievements": [_esc(a) for a in e.get("achievements", [])],
        }

    def _clean_proj(p: dict) -> dict:
        proj_skills = p.get("skills", [])
        if selected_lower:
            proj_skills = sorted(
                proj_skills, key=lambda s: s.lower() not in selected_lower
            )
        return {
            "name": _esc(p.get("name", "")),
            "description": _esc(p.get("description", "")),
            "skills": [_esc(s) for s in proj_skills],
            "links": p.get("links", []),
        }

    projects = profile.get("projects", [])
    if selected_lower:
        projects = sorted(
            projects,
            key=lambda p: -sum(1 for s in selected_lower if s.lower() in [x.lower() for x in p.get("skills", [])]),
        )

    def _clean_edu(e: dict) -> dict:
        return {
            "institution": _esc(e.get("institution", "")),
            "degree": _esc(e.get("degree", "")),
            "field": _esc(e.get("field", "")),
            "location": _esc(e.get("location", "")),
            "start_date": _esc(e.get("start_date", "")),
            "end_date": _esc(e.get("end_date", "")),
        }

    return {
        "personal": personal,
        "summary": _esc(profile.get("summary", "")),
        "field": _esc(profile.get("field", "")),
        "tech_stacks": [_esc(s) for s in ts],
        "skills_by_category": skills_by_category,
        "experience": [_clean_exp(e) for e in experience],
        "projects": [_clean_proj(p) for p in projects],
        "education": [_clean_edu(e) for e in profile.get("education", [])],
        "certifications": [
            {"name": _esc(c.get("name", "")), "issuer": _esc(c.get("issuer", "")), "year": _esc(c.get("year", ""))}
            for c in profile.get("certifications", [])
        ],
    }


def render_latex(context: dict) -> str:
    template = _env.get_template("resume.tex.j2")
    return template.render(**context)


def compile_pdf(latex_source: str) -> bytes:
    """Compile LaTeX source to PDF bytes using pdflatex. Raises RuntimeError on failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = Path(tmpdir) / "resume.tex"
        tex_path.write_text(latex_source, encoding="utf-8")

        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_path)],
            capture_output=True,
            timeout=60,
        )
        pdf_path = Path(tmpdir) / "resume.pdf"
        if result.returncode != 0 or not pdf_path.exists():
            log = result.stdout.decode(errors="replace") + result.stderr.decode(errors="replace")
            # Surface the first error line for easier debugging
            error_line = next((l for l in log.splitlines() if l.startswith("!")), log[:500])
            raise RuntimeError(f"pdflatex failed: {error_line}")

        return pdf_path.read_bytes()


def generate_resume_pdf(profile: dict, tech_stacks: list[str] | None = None) -> bytes:
    """End-to-end: profile dict → PDF bytes."""
    context = build_context(profile, tech_stacks)
    latex_source = render_latex(context)
    return compile_pdf(latex_source)
