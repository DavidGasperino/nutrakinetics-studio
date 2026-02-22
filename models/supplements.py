from models._compat import warn_legacy_import

warn_legacy_import("models.supplements", "nutrakinetics_studio.supplements")

from nutrakinetics_studio.supplements import *  # noqa: F401,F403
