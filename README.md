# ADK DB Buddy

DB Buddy is a chatbot agent that demonstrates how to connect to multiple data sources using the Google Agent Development Kit (ADK). This agent can interact with a Cloud SQL for PostgreSQL database, a Cloud SQL for SQL Server database (both using Application Integration connectors), and a Retrieval-Augmented Generation (RAG) engine.

This agent makes use of the following source data:
* Cloud SQL for Postgres database hosting a subset of NYC taxi trip data (containing information such as date, tip amount, distance, etc)
* Cloud SQL for SQL Server database hosting synthetic data that provides weather conditions (overall weather condition, low/high temperatures) for the days represented in the NYC taxi dataset
* Vertex AI RAG ENGINE hosting mutliple unstructure files (document, presentation, PDF, json) with synthetic data describing which car/model should be used for each weather condition

The agent will allow you to query the above data individually and perform joins across datasets that would normally not be connected without major coding efforts.

This is a personal project and is not endorsed by Google.  No warrantees here.  Use at your own risk.  You may want to 'Stop' your Cloud SQL Instances when not in use to save consumption charges while you are testing out this code.


## Features

*   **Multi-Tool Connectivity:** Demonstrates the use of Application Integration and RAG connectors within a single agent.
*   **Natural Language Interaction:** Ask questions about your data in plain English.
*   **PostgreSQL and SQL Server Support:** Connect to and query both PostgreSQL and SQL Server databases via Application Integration.
*   **Retrieval-Augmented Generation (RAG):** Utilizes a RAG engine to provide answers from a corpus of documents.
*   **Joined Queries:** Can join information from the different data sources to answer complex questions.
*   **Secure Connections:** Uses IAM database authentication for secure connections to your Cloud SQL instances.

## Architecture
<img width="2184" height="1340" alt="image" src="https://github.com/user-attachments/assets/878bffe4-4d44-4d03-8ff3-0f4e66164b7f" />

DB Buddy is built on the following key technologies:

*   **Google Agent Development Kit (ADK):** The core framework for building the conversational agent.
*   **Google Vertex AI hosting Gemini 2.5 Flash:** Provides the powerful Large Language Models (LLMs) that power the agent's natural language understanding and generation capabilities.
*   **Google Vertex AI Search and Conversation:** Used to create the RAG engine.
*   **Google Cloud SQL:** The managed database service used for both PostgreSQL and SQL Server.
*   **Google Application Integration Connectors:** Used to create connectors for the PostgreSQL and SQL Server databases.

## Getting Started

Follow these steps to get DB Buddy up and running.

### Prerequisites

* Google Cloud Project
* IDE (vscode, etc)


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

The `deploy_commands.sh` script contains all the necessary commands to deploy the required infrastructure and populate the databases. Please execute the commands in the script one by one, as some services take time to provision.

3.  **Set up the Integration Connectors:**
    The Application Integration connectors for PostgreSQL and SQL Server must be set up in your Google Cloud project. Please follow the instructions in the [Application Integration documentation](https://cloud.google.com/application-integration/docs/connectors) Here are more detailed steps.
    **Cloud SQL - PostGres**
    * Click Create New under **Integration Connectors** (ensure you select - Cloud SQL - PostgreSQL)
      <img width="886" height="1209" alt="image" src="https://github.com/user-attachments/assets/d5d1b19d-97df-4d1c-8022-0af3df81910e" />
      <img width="886" height="1209" alt="image" src="https://github.com/user-attachments/assets/2cf89aeb-9d2c-4ac6-bec0-f69c656c5c8c" />
      <img width="886" height="853" alt="image" src="https://github.com/user-attachments/assets/f84c3feb-e001-4e6e-8a3c-c7f5b31b7b01" />
    * Click Save
    **Cloud SQL - SQL Server**
    * Repeat the process above, but chose Cloud SQL - SQL Server

4. **Set up the Application Integration:**
    * Under Templates, click Click Connection Tool
      <img width="1076" height="606" alt="image" src="https://github.com/user-attachments/assets/171a0607-1464-4ed1-9de3-f42b4268fdca" />
    * Click Use Template
      <img width="939" height="402" alt="image" src="https://github.com/user-attachments/assets/d66fd1cb-913b-4b16-aaa2-073002a33a73" />
    * Name the integration "ExecuteConnection" (must be exactly this name)  Do not make ANY configuration changes.  This integration is designed specifically for ADK and will handle all connectivity.
    * You are complete with the connectivity setup.  
### Deployment Commands

This project includes a `deploy_commands.sh` file that contains the necessary commands to deploy the agent. Please note that this script is not intended to be run all at once. The commands should be executed one section at a time to allow for the timing of individual service deployments.

## Running the Agent
From the root of the project (folder above the db_buddy folder), run the following
```
adk web
```

At that point, click the link to the localhost presented in the terminal and you can
begin interacting with the agent.  Here is a sample interaction:

> **User:** hi

**Agent:** Hello! How can I help you today?

> **User:** what are the days that are present for NYC taxi rides

**Agent:** The days present for NYC taxi rides are:

| ride_date  |
|------------|
| 2020-02-13 |
| 2020-04-20 |
| 2020-07-10 |
| 2020-08-01 |
| 2020-09-12 |
| 2020-12-04 |
| 2021-06-18 |
| 2021-07-09 |

> **User:** what is the weather from NYC for those days

**Agent:** Here is the weather for the specified days:

| travel_date | weather |
|-------------|---------|
| 2020-02-13  | sunny   |
| 2020-04-20  | windy   |
| 2020-07-10  | sunny   |
| 2020-08-01  | rain    |
| 2020-09-12  | snow    |
| 2020-12-04  | snow    |
| 2021-06-18  | sunny   |
| 2021-07-09  | rain    |

> **User:** what are the recommended cars to use for these days

**Agent:** Here are the recommended cars for each day based on the weather conditions:

| travel_date | weather | Car Manufacturer | Car Model        |
|-------------|---------|------------------|------------------|
| 2020-02-13  | sunny   | Mazda            | MX-5 Miata       |
| 2020-04-20  | windy   | Jeep             | Grand Cherokee   |
| 2020-07-10  | sunny   | Mazda            | MX-5 Miata       |
| 2020-08-01  | rain    | Subaru           | Forrester        |
| 2020-09-12  | snow    | Volvo            | XC-90            |
| 2020-12-04  | snow    | Volvo            | XC-90            |
| 2021-06-18  | sunny   | Mazda            | MX-5 Miata       |
| 2021-07-09  | rain    | Subaru           | Forrester        |

> **User:** add a column for a possible insight for why this car would be good for the weather on that day

**Agent:** Here are the recommended cars for each day, along with an insight into why they would be good for the weather on that day:

| travel_date | weather | Car Manufacturer | Car Model        | Insight                                                                                             |
|-------------|---------|------------------|------------------|-----------------------------------------------------------------------------------------------------|
| 2020-02-13  | sunny   | Mazda            | MX-5 Miata       | A convertible is perfect for enjoying sunny weather.                                                |
| 2020-04-20  | windy   | Jeep             | Grand Cherokee   | A heavier, more stable SUV can provide better handling and control in windy conditions.               |
| 2020-07-10  | sunny   | Mazda            | MX-5 Miata       | A convertible is perfect for enjoying sunny weather.                                                |
| 2020-08-01  | rain    | Subaru           | Forrester        | Subaru's symmetrical all-wheel drive system offers excellent traction and stability in rainy conditions. |
| 2020-09-12  | snow    | Volvo            | XC-90            | Volvos are known for their safety features and robust performance, making them suitable for snowy roads. |
| 2020-12-04  | snow    | Volvo            | XC-90            | Volvos are known for their safety features and robust performance, making them suitable for snowy roads. |
| 2021-06-18  | sunny   | Mazda            | MX-5 Miata       | A convertible is perfect for enjoying sunny weather.                                                |
| 2021-07-09  | rain    | Subaru           | Forrester        | Subaru's symmetrical all-wheel drive system offers excellent traction and stability in rainy conditions. |


## Project Structure
```
/
├───.gitignore
├───README.md
├───rename_env
├───requirements.txt
├───db_buddy/
│   ├───__init__.py
│   ├───agent.py
│   ├───prompts.py
│   ├───tools_custom.py
│   ├───tools_native.py
│   └───__pycache__/
├───connector_deployment/
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