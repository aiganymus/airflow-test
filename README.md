# Airflow Demo (GitHub Codespaces Edition, Apache Airflow 3.1.3)

This project demonstrates how to run Apache Airflow 3.1.3 inside GitHub Codespaces and how to organize DAGs and pipeline scripts for a simple data pipeline (API + Web Scraping + SQLite + CSV Export).

---

## 1. GitHub Student Developer Pack (optional)

Since you are a student, you can get extended Codespaces limits here:  
https://education.github.com/pack

---

## 2. Prepare Your Repository

1. Install Git on your local machine https://git-scm.com/install/
2. Create a new empty GitHub repository and upload this folder.  

---

## 3. Using GitHub Codespaces

1. Go to: https://github.com/features/codespaces  
2. Click **New Codespace**  
3. Select your repository  
4. Codespace will open in VS Code Web. But you need to connect using VS Code Desktop.

---

## 2. VS Code Setup (IMPORTANT)

1. Install VS Code: https://code.visualstudio.com/
2. Install the **GitHub Codespaces** extension:
   - Open VS Code → Extensions → search "Codespaces" → Install
3. In the Activity Bar (left side), click **Remote Explorer**
4. You will see your Codespace → click **Connect**
5. VS Code will open a remote development session running inside Codespaces.

### Recommended VS Code Extensions inside the Codespace:
- **Python**
- **Pylance**
- **Black Formatter**
- **isort**
- **SQLite Viewer**
- **GitLens**
- **EditorConfig**

---

## 4. Create Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas requests beautifulsoup4 apache-airflow-stubs
```

`apache-airflow-stubs` improves code completion in VS Code.  

### Configure Python interpreter in VSCode:
After creating `.venv`:

```
Ctrl + Shift + P → Python: Select Interpreter → choose .venv/bin/python
```

This enables linting, autocomplete, stubs for Airflow, etc.

---

## 5. Install Apache Airflow

```bash
export AIRFLOW_HOME=/workspaces/<your-repo>/airflow
mkdir -p $AIRFLOW_HOME

AIRFLOW_VERSION=3.1.3
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

---

## 6. Create the DAGs directory

```bash
mkdir -p $AIRFLOW_HOME/dags
airflow config get-value core dags_folder
```

Expected output:
```
/workspaces/<your-repo>/airflow/dags
```

---

## 7. Run Airflow

```bash
airflow standalone
```

This will:
- initialize the metadata database  
- start the webserver  
- start the scheduler  
- create an admin user  
- print login credentials  

UI link (auto-forwarded):  
```
http://localhost:8080
```

---

## 8. Recommended Project Structure

```
<repo>/
├─ airflow/
│  ├─ airflow.db
│  ├─ airflow.cfg
│  ├─ dags/
│  │   └─ demo_api_scrape_merge/
│  │        ├─ dag.py
│  │        └─ pipeline.py
│  └─ logs/
├─ .venv/
└─ README.md
```

Each DAG should live in its own folder with all helpers/pipeline modules.

---

## 9. Running Your Demo DAG

1. Open Airflow UI  
2. Enable DAG: `demo_api_scrape_merge`  
3. Click **Trigger DAG**  
4. Inspect logs and Graph View  
5. Output files (SQLite DB, CSV) appear in the DAG folder

---

## 10. Notes

- Do not commit `airflow.db` or `logs/`  
- Codespaces forwards ports automatically  
- `airflow standalone` is the easiest way to run Airflow without Docker
