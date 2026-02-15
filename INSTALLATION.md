# Installation – Medical Intelligence Platform

## Prerequisites

- Python 3.10+
- PostgreSQL 14+
- (Optional) Docker, Docker Compose
- (Optional) Telegram API credentials (api.telegram.org)

## Local setup

### 1. Clone and enter project

```bash
git clone <repo-url>
cd medical-intelligence-platform
```

### 2. Create virtualenv and install dependencies

**Linux/macOS:**

```bash
./scripts/setup.sh
```

**Windows (PowerShell):**

```powershell
.\scripts\setup.ps1
```

**Manual:**

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\Activate.ps1 on Windows
pip install -U pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-nlp.txt
pip install -e .
```

### 3. Environment variables

```bash
cp .env.example .env
```

Edit `.env` and set at least:

**Production:** Run `python scripts/validate_env.py --load-env --production` before deploy to validate required and recommended vars.

- `DATABASE_URL`: PostgreSQL connection string
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`: From https://my.telegram.org
- `TELEGRAM_SESSION_STRING` or phone for login (if scraping)

See `.env.example` for all options.

### 4. Database

```bash
python scripts/setup_db.py
python scripts/seed_data.py   # optional sample data
```

### 5. dbt (optional)

```bash
cd dbt
cp profiles.yml.example profiles.yml   # set target connection
dbt deps
dbt run
```

### 6. Run services

- **API:** `uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000`
- **Dashboard:** `streamlit run dashboards/streamlit_app.py`
- **Dagster:** `dagster dev -m src.orchestration.definitions`

## Docker

```bash
docker-compose up -d
```

See `docker-compose.yml` and `Dockerfile` for service definitions.

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
