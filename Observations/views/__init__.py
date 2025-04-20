# Observations/views/__init__.py
from .views_home import *
from .views_observation import *
from .saisie_observation_view import *
from .view_transcription import *

# Import deprecated views with a warning
import warnings
from .views_saisie_old import *

warnings.warn(
    "The module views_saisie_old is deprecated and will be removed in a future version. "
    "Use saisie_observation_view instead.",
    DeprecationWarning,
    stacklevel=2
)
