# Release verification

Candidate: 1.2.0-beta.1. This page records evidence, not a blanket claim of all-platform support.

As of 2026-10-22 (Cairo; 2026-10-21 UTC), local Windows source verification passed all 26 regression tests. A real native Windows Qt source run processed both original synthetic fixtures using small, saved SRT preserving the reference words/diacritics, and recovered from invalid audio. This development run used the preserved development environment; it does not certify the new packaged media runtime. Examples returned nonzero low-confidence fractions and require timing review.

Native release builds, installed-copy checks, OS-network-denial results, resolved dependencies, screenshots, and hashes are recorded in platform verification assets on the release once successful. Until those assets and the matching installer are present and reviewed, packaged verification remains outstanding. The older private 1.1.1 Mac build is retained separately and is not proof for this release.

Automated native GUI acceptance sends Qt drag/drop and mouse events to real widgets, uses real QThreads, model inference and the GUI's actual SRT save path. It is not a human test of every OS file picker or editing application. Native restart and CLI are separate processes. The native packaging recipe opens generated SRT in the platform text editor; process observation alone does not certify every subtitle or video editor. MSA/Egyptian examples use a synthetic Arabic voice and are not a dialect accuracy benchmark.

The source regression suite covers diacritics, repetition anchors, pause boundaries, mismatched/unmatched text and silence fallback, invalid/missing inputs, save failure, close deferral, and bundle lookup. There is no cancellation feature to test. Unknown media formats, all dialects, old target hardware performance, Windows ARM, Apple Silicon and Linux are not certified.
