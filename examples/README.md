# Synthetic Arabic examples

`msa.wav` + `msa.txt` use original Modern Standard Arabic wording and diacritics.
`egyptian.wav` + `egyptian.txt` use original Egyptian Arabic wording. Both were
synthesized with eSpeak NG 1.52.0's native `sem/ar` formant voice; the second is not a
claim of an authentic Egyptian accent. Neither file is a private recording, a
customer clip, or a sample copied from Elkholasa's content library.

The project dedicates these original texts and generated waveforms under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). The generator's
source code remains under the repository MIT license. eSpeak NG is a separate
GPL tool; its executable/voice data are not bundled with the application or these
examples. [GNU's output explanation](https://www.gnu.org/licenses/gpl-faq.html#GPLOutput)
distinguishes running a program from copying program material into its output.

Each WAV includes half a second of leading and trailing silence. Reproduce the
files with `python tools/generate_examples.py --espeak /path/to/espeak-ng`.
`provenance.json` records origins and hashes. The historical
`verification/speech-sample.wav` was excluded because its origin could not be
verified. The synthetic samples are smoke/behavior fixtures, not a speech-quality
or timing-accuracy benchmark. Inspect actual release test results before drawing
conclusions about recognition quality.
