# API Routers package for Azure Voice Cloning API

from . import voice_management
from . import synthesis
from . import lexicon

__all__ = [
    "voice_management",
    "synthesis",
    "lexicon"
]
