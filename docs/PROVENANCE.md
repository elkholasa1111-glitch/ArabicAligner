# Source and maintenance provenance

The first public import combines two existing private editions; it is not a
rewrite or evidence of a long public contribution history.

- The preserved private Windows source has version 1.1.1. Existing installer
  verification records are dated 2026-09-29. It was found as unversioned source
  files alongside the actual two-model Windows installer and a USB source copy.
- The preserved private macOS repository is `elkholasa1111-glitch/ArabicAligner-macOS`.
  Its three commits are `63893c591de5f928039309f1338b85c485fe7a02`,
  `e89d50752c7a274db7350e266cbf9fb0a1739c79`, and
  `3bd80024fee9548b70dc4c5942c1e30b2ab6d1de`, recorded on 2026-10-20. That repository and its history are retained privately.
- Both editions share the same normalization, matching, segmentation, and SRT
  modules. The Windows edition offers two models; the macOS edition intentionally
  offers only small. Platform packaging and resource lookup are distinct.

Mahmoud Hussein Attay Elsayed identifies himself as the maintenance owner and
has confirmed **Elkholasa** as the original application rights holder. He
authorized the MIT choice for owned application code. Company ownership and maintenance responsibility do not imply personal authorship of every file. Existing author notices and
third-party copyrights remain applicable.

The public repository starts with a reviewed source import. It does not publish
private operating reports, local build paths, account details, or an old speech
fixture whose origin could not be established. Original histories and source
snapshots were backed up before this import. No original repository was deleted,
force-pushed, or rewritten. The import does not conceal a known credential leak;
security findings and any required remediation are handled separately.
