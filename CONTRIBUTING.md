# Contributing to ArabicAligner

Bug reports, clearer instructions, redistributable Arabic examples, regressions, and packaging improvements all help. ArabicAligner is maintained by [Mahmoud Hussein Attay Elsayed](MAINTAINERS.md) for Elkholasa.

Follow the [community conduct guidelines](CODE_OF_CONDUCT.md) in project discussions.

## Before changing the code

Check existing issues and the [roadmap](docs/ROADMAP.md). For a substantial change, open a feature request describing the user problem and expected behavior first. Read [Development](docs/DEVELOPMENT.md), [Architecture](docs/ARCHITECTURE.md), and [Licensing](docs/LICENSING.md).

Preserve these behaviors:

- Keep supplied Arabic words and diacritics in the SRT.
- Keep subtitle times valid, ordered, and nonoverlapping.
- Keep processing local and preserve platform-specific model selections.
- Keep dependency licenses, source availability, and fixture provenance accurate.

## Check a change

With the development environment installed:

```sh
python tests/test_smoke.py
python -m unittest discover -s tests -v
python tools/check_source.py
```

Headless GUI tests use `QT_QPA_PLATFORM=offscreen`. Native package acceptance uses the real OS plugin and model inference; source tests alone do not verify an installed application.

For a timing bug, add a deterministic regression using invented words and timestamps. For audio changes, use a redistributable fixture with documented provenance and check the complete audio + original reference text → SRT path. State the actual OS, architecture, model, command, and result. Keep untested platforms explicit.

## Submit a pull request

Describe the problem, resulting behavior, and validation. Keep the diff focused and explain platform or model differences. The maintainer reviews and accepts changes; package builds are deliberate release operations, separate from untrusted PR jobs.

Review and test your contribution before submission. Commit identities and attribution should reflect the people or organizations responsible; preserve existing notices and identify copied code and its license.

By contributing, you confirm permission to submit the material under its applicable license. Owned application changes use MIT. New examples need explicit redistribution terms and a documented origin. Keep private recordings, scripts, credentials, account details, weights, build environments, and diagnostic archives out of public PRs and issues. Follow [Security](SECURITY.md) for sensitive reports.
