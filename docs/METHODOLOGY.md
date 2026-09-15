# Methodology Notes

## Design principle
The model intentionally separates **underlying process quality** from **reported quality**.

The reporting gap is represented as a transparent heuristic function of:
- target pressure;
- gaming susceptibility; and
- the relative contribution of classification, timing and sampling mechanisms.

For month *t*, the maximum illustrative gap is the actual defect rate multiplied
by target pressure, gaming susceptibility, a fixed scale factor of 0.85, and a
linearly increasing maturity factor. Mechanism weights are normalised to sum to
one; if all three weights are zero, the gap is divided equally. The target defect
rate is a visual reference line and does not itself alter the simulated process.

The purpose is explanatory: to make the logic visible and adjustable.

## SPC simulation
The SPC module generates synthetic binomial defect data and then compresses unusual observations toward a baseline to illustrate how reclassification or reporting distortion can weaken visible signals.
The displayed three-sigma control limits are calculated from the unsanitised
observations. A fixed seed makes identical configurations reproducible.

## Cost of Quality
The cost module compares internal failure cost with external failure cost and demonstrates how hidden internal failures can move downstream rather than disappear.
The incremental estimate equals the hidden internally detected defects multiplied
by the difference between external and internal unit failure costs. It can be
negative when a user deliberately assumes external failure is cheaper.

## Metric Integrity Score
The score is a heuristic rather than a validated index. It combines four vulnerability dimensions into a 0–100 integrity score. The weights are explicitly coded so users can inspect and change them.
The current weights are 20% single-metric dependence, 30% stakes, 30%
manipulability and 20% weak customer linkage. Inputs are validated on a 0–1
scale and the weights sum to one.

## Numerical safeguards
All rates are represented internally as decimal fractions. Configuration values
are checked before calculation, generated rates are bounded to 0–1, sample and
period counts must be positive, and cost assumptions must be finite and
non-negative. These safeguards catch invalid scenarios; they do not constitute
empirical validation of the model.

## Responsible interpretation
Results are illustrative. The tool should not be used to infer intentional gaming, fraud or misconduct by a person or organisation without independent evidence.

## Scenario presets and exports
Presets are named bundles of the same user-adjustable assumptions; they do not
introduce separate models or empirical calibration. Editing any preset value
returns the interface to Custom mode. CSV, JSON and Markdown exports are
deterministic for identical inputs and seeds, omit timestamps, and include the
educational-use disclaimer in the portable summaries.

Preset comparisons also include an explicit five-answer Metric Audit bundle.
Those answers are hypothetical preset inputs; they are not inferred from the
Metric Integrity Score or from empirical evidence. Comparison deltas are always
defined as Scenario B minus Scenario A. Shared cost assumptions are applied to
both scenarios so the cost contrast is attributable to scenario inputs rather
than different unit-cost choices.

## User-provided CSV data

The import workflow is exploratory visualisation using user-provided data. It
accepts `period` and `reported_rate`, with optional `actual_rate` and
`target_rate`. Rates must be finite decimal fractions from 0 to 1 inclusive.
Columns, rows, and ordering are validated without silent repairs. The original
period order is preserved.

When `actual_rate` is absent, the app does not estimate or fabricate it and does
not calculate a reporting gap. An observed difference between supplied actual
and reported rates is descriptive only and is not evidence of gaming, intent,
fraud, or misconduct.

## Academic foundations

The references below inform the app's questions about target fixation,
performance measurement, customer linkage, systems, and variation. The app does
not implement or reproduce an empirical model from any of them.

- Goodhart, C. A. E. (1975). *Problems of Monetary Management: The U.K.
  Experience.* Papers in Monetary Economics, Volume I, Reserve Bank of Australia.
- Mattson, B. W., Bushardt, R. L., & Artino, A. R. Jr. (2021). [When a Measure
  Becomes a Target, It Ceases to Be a Good
  Measure](https://doi.org/10.4300/JGME-D-20-01492.1). *Journal of Graduate
  Medical Education, 13*(1).
- Elton, L. (2004). [Goodhart's Law and Performance Indicators in Higher
  Education](https://doi.org/10.1080/09500790408668312). *Evaluation & Research
  in Education, 18*(1–2), 120–128.
- Fisher, N. I. (2021). [Performance Measurement: Issues, Approaches, and
  Opportunities](https://doi.org/10.1162/99608f92.c28d2a68). *Harvard Data
  Science Review, 3*(4).
- Fisher, N. I., & Kordupleski, R. E. (2019). [Good and Bad Market Research: A
  Critical Review of Net Promoter Score](https://doi.org/10.1002/asmb.2417).
  *Applied Stochastic Models in Business and Industry, 35*(1), 138–151.
- The W. Edwards Deming Institute. [The Deming System of Profound
  Knowledge](https://deming.org/explore/sopk/).

The Fisher and Kordupleski joint paper is correctly listed as 2019. Fisher's
broader performance-measurement article is the 2021 publication. These sources
do not validate this simulator's chosen coefficients, scores, presets, or
conclusions.
