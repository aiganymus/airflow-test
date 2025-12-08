# Airflow + Kafka Demo (GitHub Codespaces Edition)

This project demonstrates how to run **Apache Airflow** and **Apache Kafka** together inside **GitHub Codespaces**, and how to build a simple end-to-end data pipeline (for example, REST API → Pandas → Kafka). It combines the workflows from two separate guides into one unified setup.

> **Important:** This README intentionally contains only shell / Linux commands.  
> You are expected to write your own Python code (producers, consumers, Airflow tasks) in separate files.

---

## 1. Prepare Your Repository

1. Install Git on your local machine.  
2. Create a new GitHub repository (or reuse an existing one).  
3. Clone the repository locally and push any initial folder structure you need.

Example (locally, on your machine):

```bash
git clone git@github.com:<your-username>/<your-repo>.git
cd <your-repo>
git add .
git commit -m "Initial commit"
git push origin main
```

Replace `<your-username>` and `<your-repo>` with your actual GitHub username and repository name.

---

## 2. Create a GitHub Codespace

1. Open your repository on GitHub.  
2. Click the green **Code** button → **Codespaces** tab → **Create codespace on main**.  
3. Wait until the Codespace environment is created and VS Code (web) opens.  
4. (Optional but recommended) Open the Codespace in **VS Code Desktop** using the *GitHub Codespaces* extension.

You will be working inside the remote Codespace environment for all further steps.

---

## 3. Recommended VS Code Extensions (inside the Codespace)

Within the Codespace (remote VS Code session), install the following extensions (if not already available):

- **Python**  
- **Pylance**  
- **Black Formatter**  
- **isort**  
- **SQLite Viewer**  
- **GitLens**  
- **EditorConfig**  

These extensions improve code quality, formatting, and navigation.

---

## 4. Create and Configure a Python Virtual Environment

Inside the Codespace terminal (from your repo root):

1. Create a virtual environment:

```bash
python3 -m venv .venv
```

2. Activate the virtual environment:

```bash
source .venv/bin/activate
```

3. Configure VS Code to use this interpreter:

- Press `Ctrl + Shift + P` (or `Cmd + Shift + P` on macOS).  
- Choose **Python: Select Interpreter**.  
- Select the interpreter from `.venv` (it should look like `.venv/bin/python`).

All further Python packages (including Airflow) will be installed into this virtual environment.

---

## 5. Install and Configure Apache Airflow

### 5.1 Set `AIRFLOW_HOME`

Decide where Airflow will store its files. A common choice in Codespaces is:

```bash
export AIRFLOW_HOME=/workspaces/<your-repo>/airflow
mkdir -p "$AIRFLOW_HOME"
```

Replace `<your-repo>` with your repo folder name under `/workspaces`.

> You can add the `export AIRFLOW_HOME=...` line to your shell profile (e.g. `~/.bashrc`) if you want it to persist. In Codespaces, you can also re-run this command in each new terminal.

### 5.2 Install Airflow with constraints

Apache Airflow requires installing with compatibility constraints. With the virtual environment already active and `AIRFLOW_HOME` set, run:

```bash
AIRFLOW_VERSION=3.1.3
PYTHON_VERSION="$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"

pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
```

This will install Airflow and compatible dependencies into `.venv`.

### 5.3 Create the DAGs folder

Create the DAGs directory under `AIRFLOW_HOME`:

```bash
mkdir -p "$AIRFLOW_HOME/dags"
```

You can verify the configured DAGs folder with:

```bash
airflow config get-value core dags_folder
```

Airflow’s structure will look like:

```text
/workspaces/<your-repo>/
└─ airflow/
   ├─ airflow.db
   ├─ airflow.cfg
   ├─ dags/
   └─ logs/
```

Place your DAG Python files inside `airflow/dags/`.

---

## 6. Run Airflow in Codespaces

With the virtual environment active and `AIRFLOW_HOME` set, start Airflow in standalone mode:

```bash
airflow standalone
```

This command will:

- Initialize the Airflow metadata database.  
- Start the Airflow webserver.  
- Start the scheduler.  
- Create an admin user and print credentials in the terminal.

Codespaces will automatically detect and forward the webserver port (usually 8080). Use the forwarded URL shown in the Ports panel to access Airflow UI in your browser.

> Keep this terminal open; Airflow will stop if you close it or interrupt the process.

---

## 7. Install Java (Required for Kafka)

Apache Kafka requires Java. Check whether Java is already available:

```bash
java -version
```

If Java is not installed or the command is not found, install OpenJDK:

```bash
sudo apt-get update
sudo apt-get install -y openjdk-11-jdk
```

After installation, verify again:

```bash
java -version
```

---

## 8. Download and Extract Kafka

From your repository root folder (inside Codespaces), navigate to the workspace:

```bash
cd /workspaces/<your-repo>
```

Download a Kafka binary (example: Scala 2.13, Kafka 4.1.1):

```bash
wget https://dlcdn.apache.org/kafka/4.1.1/kafka_2.13-4.1.1.tgz
```

Extract the archive:

```bash
tar -xzf kafka_2.13-4.1.1.tgz
```

Change into the Kafka directory:

```bash
cd kafka_2.13-4.1.1
```

From now on, Kafka commands will be executed within this directory.

---

## 9. Initialize and Start the Kafka Broker

Before starting the Kafka broker for the first time, format its log directories.

### 9.1 Generate a cluster ID

```bash
KAFKA_CLUSTER_ID="$(bin/kafka-storage.sh random-uuid)"
```

### 9.2 Format the log directories

```bash
bin/kafka-storage.sh format --standalone -t "$KAFKA_CLUSTER_ID" -c config/server.properties
```

### 9.3 Start the Kafka broker

```bash
bin/kafka-server-start.sh config/server.properties
```

Leave this terminal running. This process is your Kafka broker.

---

## 10. Create a Kafka Topic

Open a **new terminal** in Codespaces for Kafka administration, and navigate to the Kafka directory:

```bash
cd /workspaces/<your-repo>/kafka_2.13-4.1.1
```

Create a topic (for example, `quickstart-events`):

```bash
bin/kafka-topics.sh --create --topic quickstart-events --bootstrap-server localhost:9092
```

Optionally, describe the topic to verify it exists:

```bash
bin/kafka-topics.sh --describe --topic quickstart-events --bootstrap-server localhost:9092
```

---

## 11. Test Kafka with Console Producer and Consumer (Optional)

You can verify that Kafka is functioning by using the built-in console tools.

### 11.1 Console producer

In one terminal (Kafka directory):

```bash
cd /workspaces/<your-repo>/kafka_2.13-4.1.1

bin/kafka-console-producer.sh --topic quickstart-events --bootstrap-server localhost:9092
```

Type some lines and press Enter after each one to send messages to the topic. To stop, press `Ctrl + C`.

### 11.2 Console consumer

In another terminal (Kafka directory):

```bash
cd /workspaces/<your-repo>/kafka_2.13-4.1.1

bin/kafka-console-consumer.sh --topic quickstart-events --from-beginning --bootstrap-server localhost:9092
```

You should see the messages that were produced by the console producer. To stop the consumer, press `Ctrl + C`.

---

## 12. Using Python with Kafka and Airflow (Conceptual)

1. Airflow DAGs (in `airflow/dags/`) define tasks that:  
   - call external REST APIs,  
   - use Pandas to transform and clean the data,  
   - send messages to Kafka topics.

2. Python producer/consumer scripts in your repository use a Kafka client library (installed into `.venv`) to publish or consume messages from Kafka.

You are free to:

- Install any Kafka client package into `.venv` (for example, `kafka-python` or similar).  
- Write your own Python scripts for sending data to Kafka and reading from Kafka.  
- Integrate these scripts into Airflow tasks.

---

## 13. Typical Terminal Layout in Codespaces

To work comfortably with this setup, it is recommended to keep **three** active terminals:

1. **Airflow terminal**  
   - Activate `.venv`.  
   - Export `AIRFLOW_HOME`.  
   - Run `airflow standalone`.  
   - Leave it running to keep Airflow webserver + scheduler alive.

2. **Kafka broker terminal**  
   - Change to `kafka_2.13-4.1.1` directory.  
   - Format storage (only once, first time).  
   - Run `bin/kafka-server-start.sh config/server.properties`.  
   - Leave it running as your Kafka broker.

3. **Work / utility terminal**  
   - Create and manage Kafka topics.  
   - Run console producers/consumers (for testing).  
   - Execute helper scripts and Airflow CLI commands.  
   - Edit files using `vim` or just keep it for git operations.

This layout allows you to run Airflow and Kafka side by side within a single Codespace.

---

## 14. Stopping and Cleaning Up

When you are done with your session:

1. **Stop console producers/consumers**  
   - Press `Ctrl + C` in each console where they run.

2. **Stop the Kafka broker**  
   - Press `Ctrl + C` in the broker terminal (where `kafka-server-start.sh` is running).

3. **Stop Airflow**  
   - Press `Ctrl + C` in the terminal running `airflow standalone`.

4. **Optional: clean Kafka log directories**  
   - If you want a fresh Kafka state next time:

```bash
rm -rf /tmp/kafka-logs
```

5. **Commit any code changes**  
   - Use `git add`, `git commit`, and `git push` to save your work.

---

You now have a working environment in GitHub Codespaces with **Apache Airflow** and **Apache Kafka** running together. You can build and experiment with real data pipelines that pull data from REST APIs, clean it with Pandas (in your own Python code), and stream it through Kafka topics orchestrated by Airflow.
