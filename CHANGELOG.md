# Changelog

## 1.2.0-beta.1 — 2026-10-22 — first public cross-platform preview

- Import the existing Windows and Intel macOS sources into one reviewed project.
- Preserve Windows small/large-v3-turbo and macOS small-only editions.
- Keep local CPU INT8 transcription, original-reference mapping, and SRT output.
- Add explicit source provenance, application MIT licensing, and separate
  third-party redistribution records.
- Add original synthetic examples, broader regressions, and intentional native
  package verification with OS-enforced network blocking.
- Build controlled FFmpeg/PyAV media dependencies for redistribution rather than
  treating existing opaque GPL-enabled executable bundles as MIT.
- Split short cues at long pauses and avoid merging across those pauses.
- Let macOS source checkouts discover their prepared platform-specific model directory.
- Expose the existing CLI through the packaged `--cli` entry point.
- Keep Windows native standard handles and terminal diagnostics while hiding the desktop launch console.
- Release Windows Ruy worker contexts before DLL TLS teardown; verify real model teardown before packaging.
- Enable runtime-dispatched Intel Ruy kernels with modern Apple Clang on Mac.

This is a preview, not a claim of independent timing accuracy or broad adoption.
The final release notes and verification records list the builds actually tested.

## 1.1.1 — historical private editions

Windows: small and large-v3-turbo, per-user Inno Setup installer, CPU-only offline
inference. Intel macOS: small only, ad-hoc signed DMG. The macOS source was first
recorded in Git on 2026-10-20; Windows files and installer evidence predate that
Git import. See [provenance](docs/PROVENANCE.md). These files are retained privately
and are not relabeled as binaries built from the new public tag.
