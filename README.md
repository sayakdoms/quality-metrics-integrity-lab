# Quality Metrics Integrity Lab

> “A quality metric can improve while the underlying process deteriorates.”

Quality Metrics Integrity Lab is an interactive Streamlit simulation for exploring Goodhart's Law, KPI gaming risk, and measurement integrity in quality management. It separates a hypothetical underlying defect process from its reported metric so users can inspect how incentives, reporting choices, and measurement-system weaknesses can create a “Quality Mirage.”

Built by **Sayak Pranab Ghosh — MBA, IIT Roorkee**.

## Project overview

The lab combines transparent calculations, deterministic synthetic simulations, scenario presets, comparison tools, and an audit checklist. Every result is educational and inspectable. The application does not claim empirical calibration, predictive accuracy, or proof of misconduct.

**Live demo:** _Streamlit Community Cloud link will be added after deployment._

## Why this project exists

Quality management depends on measures, but high-stakes targets can change the behaviour surrounding those measures. A reported KPI may then improve faster than the process it represents. This project makes that distinction visible and gives students, practitioners, and reviewers a structured way to ask what the number measures, what context changed, and what behaviour the target encourages.

## Key features

- Four coherent preset scenarios plus a fully adjustable Custom configuration.
- Seeded actual-versus-reported quality simulation with an explicit reporting gap.
- Transparent 0–100 Metric Integrity Score and risk classification.
- Classification, timing, and sampling contribution analysis.
- Synthetic p-chart comparison showing how sanitisation can suppress visible signals.
- Illustrative Cost of Quality flow from internal detection to downstream exposure.
- Five-question Metric Audit with tailored control suggestions.
- Side-by-side scenario comparison with B-minus-A deltas.
- Strict CSV import for exploratory visualisation of user-provided data.
- Deterministic CSV, JSON, and Markdown exports.

## Screenshots

Release screenshots will be added from the deployed application. Planned captures:

1. Application overview and scenario controls.
2. Quality Mirage chart and integrity diagnostic.
3. Side-by-side scenario comparison.
4. SPC Integrity view.
5. Cost of Quality view.
6. Metric Audit view.
7. Validated synthetic CSV import or methodology view.

See [screenshots/README.md](screenshots/README.md) for capture guidance.

## Analytical modules

### Quality Mirage

Simulates actual and reported defect-rate paths. The reporting gap is `actual_rate - reported_rate` and is allocated across classification, timing, and sampling mechanisms.

### Metric Integrity Score

A transparent heuristic combines single-metric dependence (20%), high-stakes consequences (30%), manipulability (30%), and weak customer linkage (20%). A higher score indicates lower modeled vulnerability. It is not an academically validated index.

### Gaming mechanisms

Shows how the final illustrative reporting gap is divided among reclassification, reporting-window timing, and sampling changes. These mechanisms are analytical possibilities, not allegations.

### SPC Integrity

Generates deterministic synthetic binomial observations and compares them with a compressed “sanitised” series using the same three-sigma limits. This illustrates how altered presentation can make a process look calmer without changing the underlying observations.

### Cost of Quality

Estimates how hiding or reclassifying internally detected defects can move hypothetical cost downstream. The calculation uses user-selected unit costs and is not a financial forecast.

### Metric Audit

Five questions examine ownership, definitions, timing, external corroboration, and behavioural response. The audit is a discussion aid, not a compliance or assurance conclusion.

## Scenario presets

- **Healthy Measurement System:** lower stakes, stronger customer linkage, and limited reporting divergence.
- **High-Pressure Defect Target:** demanding targets create greater reporting pressure.
- **Gaming-Prone KPI:** pressure and manipulability combine to widen the modeled gap.
- **Customer-Disconnected KPI:** the internal measure has weak linkage to customer outcomes.

Preset values are hypothetical bundles of the same visible controls. Each preset also has explicit hypothetical Metric Audit answers for reproducible comparison; audit classifications are not inferred from the score.

## Scenario comparison

Compare two presets or compare a preset with the current configuration. The workflow evaluates each scenario independently and displays integrity, actual and reported rates, reporting-gap contributions, SPC signals, suppressed signals, failure costs, and Metric Audit classification. Numeric deltas are always Scenario B minus Scenario A. Comparison exports include scenario names, inputs, results, deltas, and the educational disclaimer.

## CSV import

The import feature is explicitly an **exploratory visualisation using user-provided data**.

Required columns:

- `period`
- `reported_rate`

Optional columns:

- `actual_rate`
- `target_rate`

Rates must be finite decimal fractions between 0 and 1 inclusive. Column names are exact, period values must be non-empty and unique, and source ordering is preserved. The app rejects malformed inputs instead of silently repairing them. If `actual_rate` is absent, it is not fabricated and reporting-gap analysis is unavailable.

The repository includes a valid [CSV template](data/quality_data_template.csv) and a [synthetic Quality Mirage sample](data/sample_quality_mirage.csv). The sample exists only for demonstration and does not represent any real company.

## Methodology overview

The simulation uses a seeded monthly path. Actual defects combine baseline rate, linear improvement, linear deterioration, and random noise. A possible reporting gap matures over time as a transparent function of actual defects, target pressure, gaming susceptibility, and a fixed scale factor. Mechanism weights allocate that gap and are normalized to sum to one.

The presentation framework is **Measure + Context + Behaviour**:

- **Measure:** define the number precisely and triangulate it.
- **Context:** ask what changed in the process or reporting rule.
- **Behaviour:** ask what the target rewards, discourages, or makes easy to hide.

Detailed formulas and safeguards are documented in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## Model assumptions

- Rates are decimal fractions internally; `0.023` means 2.3%.
- Monthly process change is linear apart from seeded random noise.
- Reporting pressure matures gradually across the simulation horizon.
- Actual and reported rates are bounded to the inclusive range 0–1.
- SPC observations are synthetic binomial draws with fixed seeds.
- SPC limits come from unsanitised observations and are reused for comparison.
- Cost calculations assume detected failures can be shifted downstream; input costs are illustrative.
- Presets and audit answers are hypothetical teaching cases, not calibrated organizations.

## Limitations

- The models are explanatory heuristics, not empirical forecasts.
- The Metric Integrity Score is not a validated academic or industry index.
- A lower reported rate or larger reporting gap does not establish intent or misconduct.
- The SPC simulation does not replace a process-specific control plan.
- Cost results omit many prevention, appraisal, operational, and customer-impact factors.
- Imported data is not verified for provenance, completeness, or fitness for use.
- Session processing does not make confidential or personally identifiable data appropriate to upload.

## Installation

Python 3.11 or 3.12 is recommended.

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## Usage

```bash
streamlit run app.py
```

Choose a preset or adjust the sidebar controls. Review the five analytical tabs, open the scenario-comparison workflow, or upload a CSV using the documented schema. Download buttons create deterministic summaries for the active assumptions.

## Testing

```bash
pytest -q
```

The suite covers model invariants, validation boundaries, deterministic seeds, presets, diagnostics, export schemas, comparison deltas, CSV parsing, sample-data integrity, and headless Streamlit interactions. GitHub Actions runs the same suite on Python 3.12.

Compile-time sanity check:

```bash
python -m compileall app.py src tests
```

## Project structure

```text
quality-metrics-integrity-lab/
├── app.py                    # Streamlit interface and workflow orchestration
├── src/                      # Validated simulation, comparison, import, and export logic
├── tests/                    # Unit, integration, and headless Streamlit tests
├── data/                     # Synthetic sample and import template
├── docs/                     # Methodology and release-readiness notes
├── screenshots/              # Public screenshot placeholders
├── .github/workflows/        # Automated test workflow
├── requirements.txt
├── PROJECT_SPEC.md
└── LICENSE
```

## Academic foundations

The project is motivated by Goodhart's Law and quality-management concerns about target fixation, proxy measures, variation, customer-linked measures, and performance measurement. Its conceptual foundation includes:

- Goodhart, C. A. E. (1975). *Problems of Monetary Management: The U.K. Experience.* Papers in Monetary Economics, Volume I, Reserve Bank of Australia.
- Mattson, B. W., Bushardt, R. L., & Artino, A. R. Jr. (2021). [When a Measure Becomes a Target, It Ceases to Be a Good Measure](https://doi.org/10.4300/JGME-D-20-01492.1). *Journal of Graduate Medical Education, 13*(1).
- Elton, L. (2004). [Goodhart's Law and Performance Indicators in Higher Education](https://doi.org/10.1080/09500790408668312). *Evaluation & Research in Education, 18*(1–2), 120–128.
- Fisher, N. I. (2021). [Performance Measurement: Issues, Approaches, and Opportunities](https://doi.org/10.1162/99608f92.c28d2a68). *Harvard Data Science Review, 3*(4).
- Fisher, N. I., & Kordupleski, R. E. (2019). [Good and Bad Market Research: A Critical Review of Net Promoter Score](https://doi.org/10.1002/asmb.2417). *Applied Stochastic Models in Business and Industry, 35*(1), 138–151.
- The W. Edwards Deming Institute. [The Deming System of Profound Knowledge](https://deming.org/explore/sopk/).

The 2021 general performance-measurement article is authored by Fisher alone; the related Fisher and Kordupleski article was published in 2019. These sources motivate the questions explored by the lab. They do not empirically validate its coefficients, simulated scenarios, score, or outputs.

## Responsible use

- Outputs are hypothetical and analytical.
- Results are not proof of gaming, fraud, compliance failure, or misconduct.
- Synthetic examples do not represent real organizations.
- Imported datasets remain the user's responsibility.
- Avoid uploading confidential or personally identifiable information.
- The app is intended for education and exploratory quality-management analysis.

## Roadmap

- Add p, np, c, and u chart options with explicit data requirements.
- Add process-capability analysis only where distributional assumptions are visible.
- Expand sensitivity analysis for model assumptions and seeds.
- Consider a dedicated in-app methodology page if the compact expander becomes insufficient.
- Add automated browser-level visual regression checks.
- Evaluate a downloadable report format after comparison workflows stabilize.

## Release preparation

Suggested repository metadata, Git initialization commands, v0.3.0 release notes, deployment checks, and LinkedIn copy are prepared in [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md). No repository initialization, push, deployment, or remote creation has been performed.

## License

MIT. See [LICENSE](LICENSE).
