# A Global Affordability Overview 2017-2024
 
## Description
Interactive dashboard exploring the cost of a healthy diet across the world from 2017 to 2024, based on the Kaggle notebook [A Global Affordability Overview (2017–2024)](https://www.kaggle.com/code/hassanjameelahmed/a-global-affordability-overview-2017-2024).

## Dashboard
The dashboard is accessible at:
**https://food-affordability-django75.lab.sspcloud.fr**
 
## Deployment
The application deployment is automatically managed by **ArgoCD** via the GitOps repository:
https://github.com/Youssef75ensae/application-deployment
 
Any change pushed to this repository is automatically applied to the SSPCloud Kubernetes cluster.
 
## CI/CD Pipeline
- **CI**:
  GitHub Actions builds and pushes the Docker image to DockerHub on every push to `master`
  On every push and pull request, GitHub Actions runs `ruff check src tests` and `pytest` (see `.github/workflows/ci.yml`).
- **CD**: ArgoCD monitors the GitOps repository and automatically redeploys on every change
## Docker Image
https://hub.docker.com/r/youssef75ensae/food-affordability
 
## Configuration
Create a `.env` file at the root of the project with the following variables:
```
MY_BUCKET=...
CHEMIN_FICHIER=...
CHEMIN_PARQUET=...
```
## How to run

From the repository root, with [uv](https://docs.astral.sh/uv/) installed:

```bash
uv sync
uv run streamlit run src/app/app.py
```

