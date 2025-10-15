# DB Buddy

DB Buddy is a chatbot agent that allows you to interact with your PostgreSQL and SQL Server databases using natural language. It leverages the power of Google's Vertex AI and Agent Development Kit (ADK) to translate your questions into SQL queries and provide you with the answers you need.

## Features

*   **Natural Language Interaction:** Ask questions about your data in plain English.
*   **PostgreSQL and SQL Server Support:** Connect to and query both PostgreSQL and SQL Server databases.
*   **RAG-Powered Insights:** Utilizes a Retrieval-Augmented Generation (RAG) engine to provide contextually relevant information from your database documentation.
*   **Automated Deployment:** Scripts are provided to automate the deployment of the necessary cloud infrastructure on Google Cloud.

## Architecture

DB Buddy is built on the following key technologies:

*   **Google Agent Development Kit (ADK):** The core framework for building the conversational agent.
*   **Google Vertex AI:** Provides the powerful Large Language Models (LLMs) that power the agent's natural language understanding and generation capabilities, as well as the RAG engine.
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
    cp .env.example .env
    ```
2.  **Edit the `.env` file:**
    Fill in the required environment variables in the `.env` file. This will include your Google Cloud project ID, region, database instance names, and other configuration settings.

### Deployment

1.  **Deploy the database infrastructure:**
    Run the `db_deploy.py` script to create the Cloud SQL instances, databases, and RAG engine corpus.
    ```bash
    python3 deployment/db_deploy.py postgres
    python3 deployment/db_deploy.py sqlsvr
    ```
2.  **Deploy the SQL Server connector:**
    Run the `app_int_sqlsvr_deploy.py` script to deploy the Application Integration connector for SQL Server.
    ```bash
    python3 deployment/app_int_sqlsvr_deploy.py
    ```

## Usage

Once the deployment is complete, you can start the DB Buddy agent and interact with it through the command line.

```bash
# (Instructions on how to run the agent will be added here)
```

## Project Structure

```
/
├───.gitignore
├───deploy_sqlsvr_connector.sh
├───requirements.txt
├───sqlserver-connector.json
├───.git/
├───.venv/
├───cloud-sql-auth-proxy/
├───db-buddy/
│   ├───agent.py              # The main agent logic
│   ├───postgres_tools.py     # Tools for interacting with PostgreSQL
│   ├───prompts.py            # Prompts for the agent
│   └───tools.py              # Common tools for the agent
├───deployment/
│   ├───app_int_sqlsvr_deploy.py # Deploys the SQL Server connector
│   ├───db_deploy.py          # Deploys the database infrastructure
│   └───db_populate.py        # Populates the databases with sample data
├───documentation/
│   ├───postgres/
│   └───sqlsvr/
└───source-data/
    ├───postgres/
    └───sqlsvr/
```
