from models._compat import warn_legacy_import

warn_legacy_import("models.supplement_modules.base", "nutrakinetics_studio.supplement_modules.base")

from nutrakinetics_studio.supplement_modules.base import *  # noqa: F401,F403
