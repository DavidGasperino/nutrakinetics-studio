from models._compat import warn_legacy_import

warn_legacy_import("models.simulation", "nutrakinetics_studio.simulation")

from nutrakinetics_studio.simulation import *  # noqa: F401,F403
