from pathlib import Path
import re
import pytest


def test_report_templates_do_not_contain_hardcoded_metric_floats():
    """
    Principle V enforcement:
    Verify that report templates under templates/ do not contain hardcoded decimal floats
    outside Jinja2 expression blocks.
    """
    template_dir = Path("templates")
    if not template_dir.exists():
        return

    templates = list(template_dir.glob("*.j2"))
    for t_path in templates:
        with open(t_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Remove all Jinja expression blocks {{ ... }} and {% ... %}
        cleaned = re.sub(r"\{\{.*?\}\}", "", content, flags=re.DOTALL)
        cleaned = re.sub(r"\{%.*?%\}", "", cleaned, flags=re.DOTALL)

        # Look for hardcoded floating point numbers like 0.85, 94.2%, 12.34
        # (Exclude version numbers like 1.0.0 or section numbers 1. 2.)
        decimal_matches = re.findall(r"\b\d+\.\d{2,}\b", cleaned)
        assert len(decimal_matches) == 0, f"Template {t_path.name} contains hardcoded metrics: {decimal_matches}"
