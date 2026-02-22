from models._compat import warn_legacy_import

warn_legacy_import("models.parameters", "nutrakinetics_studio.parameters")

from nutrakinetics_studio.parameters import *  # noqa: F401,F403
