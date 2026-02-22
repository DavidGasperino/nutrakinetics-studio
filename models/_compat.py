from __future__ import annotations

import warnings


def warn_legacy_import(legacy_module: str, new_module: str) -> None:
    warnings.warn(
        f"{legacy_module} is deprecated and will be removed after the shim window. "
        f"Use {new_module} instead.",
        DeprecationWarning,
        stacklevel=2,
    )
