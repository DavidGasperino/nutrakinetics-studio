from models._compat import warn_legacy_import

warn_legacy_import("models.supplement_modules.default", "nutrakinetics_studio.supplement_modules.default")

from nutrakinetics_studio.supplement_modules.default import *  # noqa: F401,F403
