# Data

This directory contains only synthetic, educational CSV assets:

- `quality_data_template.csv` documents the accepted import schema with valid example rows.
- `sample_quality_mirage.csv` demonstrates an intentionally constructed pattern in which reported quality improves while the synthetic underlying process deteriorates.

Neither file represents a real company, operating process, person, or empirical finding. Do not commit proprietary, confidential, or personally identifiable data to this repository.

The import schema requires `period` and `reported_rate`. `actual_rate` and `target_rate` are optional. Rates are decimal fractions between 0 and 1 inclusive. Reporting-gap analysis is unavailable when `actual_rate` is absent.
