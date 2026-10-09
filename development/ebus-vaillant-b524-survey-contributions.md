# B524 survey profile contribution checks

This repository workflow validates profiles described in the [neutral survey method](../protocols/vaillant/ebus-vaillant-b524-survey-methodology.md).

Validate the public artifact before proposing it:

```sh
jv protocols/vaillant/fixtures/b524-bounded-survey-profile-schema-v1.json \
  protocols/vaillant/fixtures/b524-bounded-survey-<profile>-v1.json
pytest -q tests/test_b524_bounded_survey_profile.py
```

The tests automatically check phase totals for every contributed
`b524-bounded-survey-<profile>-v1.json` fixture. Discovery and extension retain
separate planned, completed and attempt counts; reused exchanges are recorded
separately and are not added to this execution's completed-job total.
