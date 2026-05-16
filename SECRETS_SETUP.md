# Secrets and local configuration

All credentials and machine-specific values in this repository are placeholders
(`CHANGE_ME_*`). Before you run anything, set the values that apply to your setup.

FHS itself runs entirely on NumPy/SciPy and does not call any external service. The only
required value is the Jupyter token; everything else is optional and only needed for
specific tooling.

## Required

| Variable | Purpose | How to obtain |
| --- | --- | --- |
| `JUPYTER_TOKEN` | Auth token for the Jupyter server (used by `make up`) | `openssl rand -hex 16` |

Set it in your shell before starting the stack:

```bash
export JUPYTER_TOKEN="$(openssl rand -hex 16)"
make up
```

## Optional

| Variable | Purpose | How to obtain |
| --- | --- | --- |
| `SONAR_TOKEN` | Local SonarQube reporting via `make quality` | <https://sonarcloud.io/account/security> |
| `SONAR_HOST_URL` | URL of your SonarQube server | provided by your Sonar instance |

## Machine-specific defaults you may want to override

- `HOST_UID` / `HOST_GID` default to `1000`. On Linux, run `id` and override if your
  user IDs differ.
- Thread counts (`OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `OMP_NUM_THREADS`,
  `NUMEXPR_MAX_THREADS`) default to `4`. Tune to your CPU.

## Reporting issues

For security reports, please use GitHub's private vulnerability reporting on this repo
rather than opening a public issue.
