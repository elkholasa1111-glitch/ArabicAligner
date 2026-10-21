"""Models shipped and offered by each platform's edition."""
import sys

MODEL_REPOS = {
    'small': 'Systran/faster-whisper-small',
    'large-v3-turbo': 'mobiuslabsgmbh/faster-whisper-large-v3-turbo',
}
# Mahmoud's MacBook Air edition intentionally ships only the fast model.
# Keep the existing Windows edition's selection intact.
MODEL_NAMES = ('small',) if sys.platform == 'darwin' else tuple(MODEL_REPOS)
MODEL_FOLDERS = tuple('models--' + MODEL_REPOS[name].replace('/', '--') for name in MODEL_NAMES)
