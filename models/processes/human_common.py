from models._compat import warn_legacy_import

warn_legacy_import("models.processes.human_common", "nutrakinetics_studio.processes.human_common")

from nutrakinetics_studio.processes.human_common import *  # noqa: F401,F403
