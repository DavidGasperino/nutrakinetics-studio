from models._compat import warn_legacy_import

warn_legacy_import("models.supplement_modules", "nutrakinetics_studio.supplement_modules")

from nutrakinetics_studio.supplement_modules import *  # noqa: F401,F403
