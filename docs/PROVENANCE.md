# Source provenance and attribution

## Existing editions

ArabicAligner combines the existing Windows and Intel macOS editions in one public source tree. Version 1.2.0-beta.1 is the first unified public preview.

| Edition | Preserved source and history |
| --- | --- |
| Windows 1.1.1 | Original source files, the two-model installer, and a USB source copy were preserved. Installer verification records date to 2026-09-29. These files did not have an existing Git history. |
| Intel macOS 1.1.1 | The private `elkholasa1111-glitch/ArabicAligner-macOS` repository and its three original commits, recorded on 2026-10-20, are retained. |

The original Mac commit IDs are `63893c591de5f928039309f1338b85c485fe7a02`, `e89d50752c7a274db7350e266cbf9fb0a1739c79`, and `3bd80024fee9548b70dc4c5942c1e30b2ab6d1de`.

The editions share normalization, reference matching, segmentation, and SRT generation. Windows retains small and large-v3-turbo; Mac intentionally retains small only. Packaging and resource lookup are platform-specific. The public import preserves these behaviors; the public history is not presented as a longer contribution history.

## Rights and responsibility

**Elkholasa** is the confirmed rights holder for the original application code and authorized its [MIT license](../LICENSE). **[Mahmoud Hussein Attay Elsayed](https://github.com/elkholasa1111-glitch)** is the confirmed primary maintainer and administers the repository. See [Maintainership](../MAINTAINERS.md) for responsibilities and contact.

Repository maintenance and rights ownership are distinct from file-level authorship. Existing contributor notices, commit records, and third-party copyrights remain in place.

## Public source scope

The public source starts with a reviewed import. Original source snapshots, private repositories, and earlier installers remain preserved. No original repository was deleted, force-pushed, or rewritten for publication.

Public examples have documented origins and redistribution terms in [examples](../examples/README.md). A previous speech fixture with unconfirmed redistribution provenance was excluded. Private recordings and operational data remain outside the public repository. Dependency and model redistribution are documented in [Licensing](LICENSING.md).
