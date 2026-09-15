import re
from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_public_version_is_consistent():
    for relative_path in (
        "app.py",
        "README.md",
        "docs/RELEASE_READINESS.md",
        "screenshots/README.md",
    ):
        assert "v0.3.0" in (ROOT / relative_path).read_text(encoding="utf-8")


def test_readme_local_links_resolve():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    links = re.findall(r"\[[^]]+\]\(([^)]+)\)", readme)
    local_links = [
        link.split("#", maxsplit=1)[0]
        for link in links
        if link and not link.startswith(("http://", "https://", "mailto:", "#"))
    ]

    assert local_links
    assert all((ROOT / link).exists() for link in local_links)


def test_academic_foundations_are_cautious_and_complete():
    methodology = (ROOT / "docs/METHODOLOGY.md").read_text(encoding="utf-8")
    normalised_methodology = " ".join(methodology.split())

    for expected in (
        "Goodhart, C. A. E. (1975)",
        "Mattson, B. W., Bushardt, R. L., & Artino, A. R. Jr. (2021)",
        "Elton, L. (2004)",
        "Fisher, N. I. (2021)",
        "Fisher, N. I., & Kordupleski, R. E. (2019)",
        "The W. Edwards Deming Institute",
    ):
        assert expected in methodology

    assert (
        "does not implement or reproduce an empirical model"
        in normalised_methodology
    )
    assert "do not validate" in normalised_methodology


def test_release_materials_include_required_publication_items():
    release_notes = (ROOT / "docs/RELEASE_READINESS.md").read_text(encoding="utf-8")

    for expected in (
        "quality-metrics-integrity-lab",
        "Release Quality Metrics Integrity Lab v0.3.0",
        "Quality Metrics Integrity Lab v0.3.0",
        "Streamlit Community Cloud deployment checklist",
        "LinkedIn Featured",
        "LinkedIn Projects",
    ):
        assert expected in release_notes


def test_publication_artifacts_are_ignored():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    for expected in (
        ".venv/",
        "__pycache__/",
        ".pytest_cache/",
        ".env",
        ".streamlit/secrets.toml",
        ".idea/",
        ".vscode/",
        "exports/",
    ):
        assert expected in gitignore


def test_deployment_dependencies_are_exactly_pinned():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()

    assert requirements
    assert all(line.count("==") == 1 for line in requirements if line.strip())
