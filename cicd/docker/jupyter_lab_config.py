# Project: FHS (Feature Hypotheses Simulation)
# Copyright: Eifel42 Stefan Zils 2026
# License: See LICENSE and README.md
#
# Disclaimer: This software is provided "as is", without warranty of any kind,
# express or implied, including but not limited to the warranties of
# merchantability, fitness for a particular purpose, and noninfringement.
# In no event shall the authors or copyright holders be liable for any claim,
# damages or other liability, whether in an action of contract, tort or
# otherwise, arising from, out of or in connection with the software or the
# use or other dealings in the software.

# Jupyter Lab Configuration for FHS Development
# This configuration provides flexible authentication for local development

import os
import secrets

c = get_config()  # noqa

# Authentication: Use environment variable or generate an ephemeral token
jupyter_token = os.environ.get("JUPYTER_TOKEN", "")
if jupyter_token:
    c.ServerApp.token = jupyter_token
    c.IdentityProvider.token = jupyter_token
else:
    generated_token = secrets.token_urlsafe(24)
    c.ServerApp.token = generated_token
    c.IdentityProvider.token = generated_token
    print(f"[fhs] Generated Jupyter token: {generated_token}")

# Network configuration
c.ServerApp.ip = "0.0.0.0"
c.ServerApp.port = 8888
c.ServerApp.open_browser = False

# CORS and security
c.ServerApp.allow_origin = ""
c.ServerApp.allow_credentials = False
c.ServerApp.disable_check_xsrf = False

# Root directory
c.ServerApp.root_dir = "/workspace"

# Enable JupyterLab by default
c.ServerApp.default_url = "/lab"

# Logging
c.ServerApp.log_level = "INFO"

# Base URL (for reverse proxy setups)
c.ServerApp.base_url = "/"

# Allow remote access only when explicitly enabled
c.ServerApp.allow_remote_access = os.environ.get(
    "JUPYTER_ALLOW_REMOTE_ACCESS",
    "0",
).lower() in {"1", "true", "yes"}
