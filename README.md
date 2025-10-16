# DB Buddy

DB Buddy is a chatbot agent that demonstrates how to connect to multiple data sources using the Google Agent Development Kit (ADK). This agent can interact with a Cloud SQL for PostgreSQL database using a custom-built connector and a Cloud SQL for SQL Server database using an Application Integration connector.

## Features

*   **Multi-Tool Connectivity:** Demonstrates the use of both custom and Application Integration connectors within a single agent.
*   **Natural Language Interaction:** Ask questions about your data in plain English.
*   **PostgreSQL and SQL Server Support:** Connect to and query both PostgreSQL and SQL Server databases.
*   **Secure Connections:** Uses the Cloud SQL Auth Proxy for secure connections to your Cloud SQL instances.

## Architecture

DB Buddy is built on the following key technologies:

*   **Google Agent Development Kit (ADK):** The core framework for building the conversational agent.
*   **Google Vertex AI:** Provides the powerful Large Language Models (LLMs) that power the agent's natural language understanding and generation capabilities.
*   **Google Cloud SQL:** The managed database service used for both PostgreSQL and SQL Server.
*   **Google Application Integration:** Used to create a connector for the SQL Server database.
*   **Cloud SQL Auth Proxy:** Ensures secure connections to your Cloud SQL instances.

## Getting Started

Follow these steps to get DB Buddy up and running.

### Prerequisites

*   [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured.
*   [Python 3.10+](https://www.python.org/downloads/)
*   An active Google Cloud project.

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/adk-db-buddy.git
    cd adk-db-buddy
    ```
2.  **Create a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  **Create a `.env` file:**
    ```bash
    cp rename_env .env
    ```
2.  **Edit the `.env` file:**
    Fill in the required environment variables in the `.env` file. This will include your Google Cloud project ID, region, and database instance names.

### Deployment

1.  **Deploy the database infrastructure:**
    Run the `db_deploy.py` script to create the Cloud SQL instances and databases.
    ```bash
    python3 deployment/db_deploy.py postgres
    python3 deployment/db_deploy.py sqlsvr
    ```
2.  **Set up the Application Integration Connector:**
    Currently, the Application Integration connector for SQL Server must be set up manually. Please follow the instructions in the [Application Integration documentation](https://cloud.google.com/application-integration/docs/connectors) to create a new connector.

### Data Population

After deploying the databases, you need to populate them with sample data. Run the `db_populate.py` script for each database:

```bash
python3 deployment/db_populate.py postgres
python3 deployment/db_populate.py sqlsvr
```

**Note:** Populating the PostgreSQL database can take up to 1 hour.

## Usage

Once the deployment and configuration are complete, you can start the DB Buddy agent and interact with it through the command line.

```bash
# (Instructions on how to run the agent will be added here)
```

## Project Structure

```
/
├───.gitignore
├───deploy_sqlsvr_connector.sh
├───README.md
├───rename_env
├───requirements.txt
├───.git/
├───.venv/
├───cloud-sql-auth-proxy/
├───db-buddy/
│   ├───__init__.py
│   ├───agent.py
│   ├───prompts.py
│   ├───tools_custom.py
│   ├───tools_native.py
│   └───__pycache__/
├───deployment/
│   ├───db_deploy.py
│   └───db_populate.py
└───source-data/
    ├───postgres/
    │   └───revenue-for-cab-drivers-100000-rows.csv
    └───sqlsvr/
        └───nyc-weather.csv
```