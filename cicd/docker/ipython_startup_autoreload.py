# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md
#
# IPython startup hook: enables hot-reload of Python modules.
#
# Loaded automatically by every IPython/Jupyter kernel via the
# profile_default/startup/ mechanism. Combined with the bind-mount
# of apps/fhs -> /workspace this gives true hot-deployment:
#   - YAML/JSON config edits  → picked up on next load_scenario() call
#   - Python source edits     → picked up on next cell execution
#
# Disable per-kernel by setting FHS_DISABLE_AUTORELOAD=1.

import os

if os.environ.get("FHS_DISABLE_AUTORELOAD", "").lower() not in {"1", "true", "yes"}:
    try:
        ip = get_ipython()  # type: ignore[name-defined]  # noqa: F821
        if ip is not None:
            ip.run_line_magic("load_ext", "autoreload")
            ip.run_line_magic("autoreload", "2")
            print("[fhs] hot-reload enabled (autoreload 2)")
    except Exception as exc:  # pragma: no cover - kernel-only path
        print(f"[fhs] autoreload setup failed: {exc}")
