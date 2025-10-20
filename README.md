# DB Buddy

DB Buddy is a chatbot agent that demonstrates how to connect to multiple data sources using the Google Agent Development Kit (ADK). This agent can interact with a Cloud SQL for PostgreSQL database, a Cloud SQL for SQL Server database (both using Application Integration connectors), and a Retrieval-Augmented Generation (RAG) engine.

## Features

*   **Multi-Tool Connectivity:** Demonstrates the use of Application Integration and RAG connectors within a single agent.
*   **Natural Language Interaction:** Ask questions about your data in plain English.
*   **PostgreSQL and SQL Server Support:** Connect to and query both PostgreSQL and SQL Server databases via Application Integration.
*   **Retrieval-Augmented Generation (RAG):** Utilizes a RAG engine to provide answers from a corpus of documents.
*   **Joined Queries:** Can join information from the different data sources to answer complex questions.
*   **Secure Connections:** Uses IAM database authentication for secure connections to your Cloud SQL instances.

## Architecture
<img width="2184" height="1340" alt="image" src="https://github.com/user-attachments/assets/1d7f13a9-cec1-4553-a82c-4063829c5713" />


DB Buddy is built on the following key technologies:

*   **Google Agent Development Kit (ADK):** The core framework for building the conversational agent.
*   **Google Vertex AI:** Provides the powerful Large Language Models (LLMs) that power the agent's natural language understanding and generation capabilities.
*   **Google Vertex AI Search and Conversation:** Used to create the RAG engine.
*   **Google Cloud SQL:** The managed database service used for both PostgreSQL and SQL Server.
*   **Google Application Integration:** Used to create connectors for the PostgreSQL and SQL Server databases.

## Getting Started

Follow these steps to get DB Buddy up and running.

### Prerequisites

*   [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed and configured.
*   [Python 3.10+](https://www.python.org/downloads/)
*   An active Google Cloud project.
*   `psql` command-line tool for PostgreSQL.
*   `sqlcmd` command-line tool for SQL Server.

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
2.  **Set up the Application Integration Connectors:**
    The Application Integration connectors for PostgreSQL and SQL Server must be set up in your Google Cloud project. Please follow the instructions in the [Application Integration documentation](https://cloud.google.com/application-integration/docs/connectors) to create them.
3.  **Deploy the RAG Engine:**
    Run the `rag_create.py` script to create the RAG engine and populate it with the source documents.
    ```bash
    python3 deployment/rag_create.py
    ```

### Data Population

After deploying the databases, you need to populate them with sample data using the provided SQL scripts.

**PostgreSQL:**

Use `psql` to connect to your database and run the population script. You will need to replace the placeholders with your actual database information from the `.env` file.

```bash
# Example using gcloud to connect
gcloud sql connect YOUR_POSTGRES_INSTANCE_NAME --user=YOUR_GCLOUD_USER --database=YOUR_POSTGRES_DB_NAME
# Once connected, run the script:
\i deployment/db_postgres_populate.sql
```

**SQL Server:**

Use `sqlcmd` to connect to your database and run the population script. You will need your instance's IP address and the password from your `.env` file.

```bash
# Example connection
sqlcmd -S YOUR_SQLSVR_INSTANCE_IP -U sqlserver -P YOUR_SQLSVR_PASSWORD -d YOUR_SQLSVR_DB_NAME -i deployment/db_sqlsvr_populate.sql
```

## Usage

Once the deployment and configuration are complete, you can start the DB Buddy agent and interact with it through the command line.

```bash
python3 -m db-buddy.agent
```

You can now ask questions that query the different data sources. The agent can also join information from the different sources to answer more complex questions.

### Example Questions

*   **Cloud SQL (PostgreSQL):** "What was the total revenue on January 15th, 2016?"
*   **Cloud SQL (SQL Server):** "What was the weather like in NYC on 2016-01-15?"
*   **RAG Engine:** "What kind of car is recommended for snowy weather?"
*   **Joined Query (PostgreSQL and SQL Server):** "What was the total revenue on the day with the most snowfall in January 2016?"
*   **Joined Query (All sources):** "On the snowiest day in January 2016, what was the total revenue and what car is recommended for that weather?"

## Project Structure

```
/
├───.gitignore
├───README.md
├───rename_env
├───requirements.txt
├───.git/
├───.venv/
├───db-buddy/
│   ├───__init__.py
│   ├───agent.py
│   ├───prompts.py
│   ├───tools_custom.py
│   ├───tools_native.py
│   └───__pycache__/
├───deployment/
│   ├───db_deploy.py
│   ├───db_postgres_populate.sql
│   ├───db_sqlsvr_populate.sql
│   └───rag_create.py
└───source-data/
    └───rag/
        ├───Taxi Car Weather Recommendation - json.json
        ├───Taxi Car Weather Recommendations - Doc.docx
        ├───Taxi Car Weather Recommendations - PDF.pdf
        └───Taxi Car Weather Recommendations - Slides.pptx
```
