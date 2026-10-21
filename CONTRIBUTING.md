# Contributing

ArabicAligner is maintained by Mahmoud Hussein Attay Elsayed for Elkholasa.
Contributions are welcome through GitHub issues and pull requests. There is no
promised response time and no separate maintenance team is implied.

Read [development](docs/DEVELOPMENT.md), [architecture](docs/ARCHITECTURE.md),
and [licensing](docs/LICENSING.md) before changing the application or packaging.
Keep changes small. Preserve Arabic reference text, diacritics, monotonic cue
times, offline inference, and the platform-specific model selections.

Run `python tests/test_smoke.py` and
`python -m unittest discover -s tests -p "test_regression*.py"` before submitting.
For a timing bug, add a small deterministic regression using invented words and
timestamps. For audio changes, use a redistributable fixture with a documented
origin and test the complete audio + original reference -> SRT path.

Include the OS, architecture, commands, and actual results in a pull request.
Do not claim macOS, Windows, Apple Silicon, or offline acceptance from a test on
another platform. Package builds are intentional release operations, not PR jobs.

Do not attach private recordings, transcripts, keys, account details, model
weights, build environments, or local diagnostic dumps to public issues.
By contributing, you confirm that you have permission to contribute the change
under its applicable license. Original application changes use MIT; preserve
third-party notices and identify copied material explicitly.
