# A Global Affordability Overview 2017–2024

## Project Overview

This project operationalizes the Kaggle notebook [A Global Affordability Overview (2017–2024)](https://www.kaggle.com/code/hassanjameelahmed/a-global-affordability-overview-2017-2024) by Hassan Jameel Ahmed into a production-ready interactive dashboard. It explores the cost of a healthy diet across countries and regions from 2017 to 2024, drawing on World Bank data to highlight global disparities in food affordability.

The dashboard was developed as part of the *Mise en production* course at ENSAE Paris by **Avner El Baz, Kwame Mbobda-Kuate, Paco Goze, and Youssef Hamzaoui**.

---

## Features

- Interactive filtering by country, region, year range, and data quality
- Global trend visualizations and regional comparisons
- Country rankings and year-over-year analysis
- Correlation heatmaps and component breakdowns
- Technical monitoring dashboard with execution logs

---

## Running the Application Locally

The only prerequisite is [uv](https://docs.astral.sh/uv/). From the repository root:

```bash
git clone https://github.com/avnerelbaz3500/A_Global_Affordability_Overview_2017_2024.git
cd A_Global_Affordability_Overview_2017_2024
uv sync
uv run streamlit run src/app/app.py
```

The application will be available at `http://localhost:8501`.

---

## Project Architecture

```
├── src/
│   ├── app/          # Streamlit application and UI components
│   ├── data/         # Data loading, filtering, and ingestion scripts
│   └── features/     # Analysis functions, plotting, and helpers
├── tests/            # Unit tests (39 tests)
├── Dockerfile        # Container definition
└── .github/
    └── workflows/
        ├── docker.yml         # CI: builds and pushes Docker image on push to master
        └── data_pipeline.yml  # Scheduled weekly data ingestion from Kaggle to S3
```

---

## CI/CD Pipeline

This project follows a GitOps approach to deployment.

**Continuous Integration** — on every push to `master`, GitHub Actions automatically builds and pushes a new Docker image to DockerHub. A separate workflow runs `ruff` linting and `pytest` on every push and pull request.

**Continuous Deployment** — the application is deployed on SSPCloud via Kubernetes. [ArgoCD](https://argo-cd.readthedocs.io/en/stable/) continuously monitors the [GitOps repository](https://github.com/Youssef75ensae/application-deployment) and automatically redeploys the application upon any configuration change.

---

## Docker Image

The public Docker image is available at:
[https://hub.docker.com/r/youssef75ensae/food-affordability](https://hub.docker.com/r/youssef75ensae/food-affordability)

---

## Testing

The test suite can be run with:

```bash
uv run pytest tests/ -v
```

39 tests covering data loading, filtering, analysis functions, plotting utilities, and dashboard presets.
