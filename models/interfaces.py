from models._compat import warn_legacy_import

warn_legacy_import("models.interfaces", "nutrakinetics_studio.interfaces")

from nutrakinetics_studio.interfaces import *  # noqa: F401,F403
