# CTI pipeline measuring sticks

Frozen ground-truth bundles used to score what the MCP CTI pipeline extracts
from a committed report. They are test fixtures, not generated artifacts: the
pipeline output is diffed against them and the delta is the work list.

**Hard rule**: every value here must be derivable from an ontology or
dictionary (MITRE ATT&CK, MITRE D3fend, STIX 2.1 open vocab, NIST controls).
If you'd need a hardcoded lookup table to produce a field, that field doesn't
belong in the measuring stick, because the pipeline can't be expected to
invent it either.

## Files

- [`blackcat-expected.stix.json`](blackcat-expected.stix.json): ground truth
  for [`tests/data/blackcat-sample.txt`](../../tests/data/blackcat-sample.txt).
  Derived once from the ATT&CK Evaluations
  `attackevals-ael/ManagedServices/alphv_blackcat` emulation plan, with the
  provenance recorded in the bundle's `x_cti_config`. Committed as-is and
  hand-edited from here on: the generator that built it has been removed, and
  the two libraries it walked were never vendored.

## What is actually scored

Both consumers read exactly one thing from the bundle, the ATT&CK
`external_id` on each `attack-pattern` object (34 techniques).

- [`tests/test_pipeline_score.py`](../../tests/test_pipeline_score.py) runs
  stage 1 offline on the sample report and asserts precision, recall and F1
  stay above their floors. This is the harness that catches an extraction
  source starting to emit noise.
- [`tests/test_fusion_recall.py`](../../tests/test_fusion_recall.py) splits
  the report in half and checks that fusing both halves beats either alone.

The bundle also carries `software`, `tool`, `infrastructure`, `user-account`,
`malware` and `relationship` objects. Nothing reads them, and the pipeline
cannot produce them: `cti_pipeline_stage2.py` emits only `identity`,
`threat-actor` and `attack-pattern`. They are retained as a record of what the
source emulation plan asserted.

## Adding a stick

Write the bundle by hand (or from a report you already have ground truth for),
commit it alongside its source text under `tests/data/`, and point a test at
the technique ids. Keep the hard rule above: no field that needs a bespoke
lookup table to justify it.

## Scope note

Hosts, accounts and domains named in a report describe the previous victim, so
they are not turned into CALDERA facts, and no per-host topology object is
emitted. CALDERA discovers facts about the operator's own estate at runtime.
