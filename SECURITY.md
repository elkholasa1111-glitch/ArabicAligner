# Security

ArabicAligner processes local, potentially untrusted audio through native media
libraries. Use the current release and do not treat a successful alignment as a
security validation of the input file. The application does not upload audio or
transcripts, require an account, or call a cloud transcription API.

Report security vulnerabilities privately using
[GitHub private vulnerability reporting](https://github.com/elkholasa1111-glitch/ArabicAligner/security/advisories/new).
If this facility is unavailable, open a public issue asking for a private
reporting channel without including the vulnerability, recordings, credentials,
or exploit material. Do not publish secrets or customer data.

This project currently has one self-identified maintainer. There is no security
response SLA. Only the current preview release receives fixes; older private
Windows/macOS installers remain historical versions, not supported releases.

Release hashes detect transfer corruption. They do not replace publisher
authentication. Windows packages are unsigned unless release notes say otherwise;
macOS builds use an ad-hoc signature and are not Apple notarized. Do not disable
OS security protections globally to install the application.
