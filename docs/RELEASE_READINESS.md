# v0.3.0 release readiness

These materials prepare the public release without initializing Git, creating a
remote repository, pushing code, or deploying the app.

## GitHub repository metadata

- Repository name: `quality-metrics-integrity-lab`
- Description: `An educational Streamlit lab for exploring Goodhart's Law, KPI gaming risk, measurement integrity, SPC signal suppression, and quality-cost trade-offs.`
- Topics: `streamlit`, `quality-management`, `goodharts-law`, `kpi`, `spc`, `data-visualization`, `simulation`, `python`, `measurement-systems`, `portfolio-project`

## Local Git initialization

Run these commands from the repository root only after reviewing the publication
contents:

```bash
git init
git branch -M main
git add .
git status
git commit -m "Release Quality Metrics Integrity Lab v0.3.0"
```

After creating the empty GitHub repository, add its actual URL and push only when
publication is authorized:

```bash
git remote add origin https://github.com/<username>/quality-metrics-integrity-lab.git
git push -u origin main
```

Never place access tokens or credentials in source files or shell history.

## Release title and notes

**Release title:** `Quality Metrics Integrity Lab v0.3.0`

Quality Metrics Integrity Lab v0.3.0 is the first publication-ready release of
the educational simulation.

- Explore five analytical views built on transparent, deterministic models.
- Compare two scenarios with clearly defined B-minus-A deltas.
- Import a strictly validated quality time series for session-scoped exploratory
  visualisation.
- Export deterministic scenario and comparison summaries as CSV, JSON, or
  Markdown.
- Review explicit methodology, limitations, responsible-use guidance, and
  academic foundations.
- Run an expanded automated suite covering calculations, validation, imports,
  exports, and headless Streamlit interactions.

All simulations remain hypothetical. The Metric Integrity Score is a heuristic,
and imported data is not validated evidence of gaming, fraud, compliance failure,
or misconduct.

## Streamlit Community Cloud deployment checklist

- Publish the reviewed repository and confirm the default branch is `main`.
- Confirm `requirements.txt`, `.streamlit/config.toml`, `app.py`, `src/`, and the
  two synthetic CSV files are present in the repository.
- In Streamlit Community Cloud, select the repository, branch `main`, and
  entrypoint `app.py`.
- Select Python 3.12 to match the tested workflow.
- Do not configure secrets; this release has no external services or API keys.
- Inspect the build log and confirm the app starts without warnings or exceptions.
- Re-run the five-tab desktop review on the deployed URL.
- Verify scenario presets, Custom controls, comparison, Metric Audit, template and
  demo downloads, valid sample import, malformed import feedback, and all export
  formats.
- Confirm the public disclaimer and methodology content remain visible.
- Add the deployed URL to the README and GitHub repository website field.
- Capture release screenshots from the deployed app using synthetic data only.

## LinkedIn Featured

**Title:** `Quality Metrics Integrity Lab — interactive measurement-integrity simulation`

**Description:** A transparent Streamlit lab exploring how a quality KPI can
improve while the underlying process deteriorates. It includes scenario
comparison, a heuristic Metric Integrity Score, gaming-mechanism decomposition,
synthetic SPC signal suppression, Cost of Quality analysis, a Metric Audit,
deterministic exports, and strict CSV visualisation. Educational simulation only;
not a forecasting or audit tool.

## LinkedIn Projects

**Description:** Designed and built Quality Metrics Integrity Lab v0.3.0, an
educational Streamlit application for examining measurement integrity in quality
management. Developed deterministic simulations, scenario comparison, SPC and
Cost of Quality views, a structured Metric Audit, validated CSV import, portable
exports, documentation, and automated tests. The project deliberately separates
hypothetical modelling from empirical claims and includes clear responsible-use
limitations.

## Final publication checklist

- Review the full staged file list with `git status` and `git diff --cached`.
- Confirm no virtual environments, environment files, secrets, caches, generated
  exports, user datasets, editor state, or OS-specific files are staged.
- Run the complete test, compile, headless smoke, import, export, link, and secrets
  checks documented in the release report.
- Capture the screenshot set described in `screenshots/README.md`.
- Add real repository and live-demo URLs only after they exist.
