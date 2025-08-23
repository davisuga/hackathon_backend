# AutoMarket: AI-Powered Landing Page Generator (v2)

AutoMarket is a durable, conversational agent that takes a transcript of a marketing briefing and generates a complete landing page, including a marketing strategy, content calendar, and AI-generated images.

This version uses **OpenRouter** for model access and persists all workflow states in a **PostgreSQL** database for durability.

## Features

-   **Briefing Synthesis**: Distills a conversation into a structured marketing brief in Markdown.
-   **Strategic Planning**: Generates a marketing strategy and content calendar in Markdown.
-   **AI Image Generation**: Creates relevant images for the landing page via OpenRouter.
-   **Web Page Generation**: Produces a complete HTML + Tailwind CSS landing page.
-   **Durable Workflows**: All steps and artifacts are persisted in a PostgreSQL database.
-   **Interactive UI**: Uses AG-UI for a real-time, step-by-step user experience.

## Prerequisites

1.  **Python 3.10+** and **`uv`**.
2.  **Docker** and **Docker Compose**.
3.  **Deno**: For running the AG-UI Dojo frontend. [Installation Guide](https://deno.com/manual/getting_started/installation).
4.  **API Keys**:
    -   **OpenRouter API Key**: Get one from [openrouter.ai](https://openrouter.ai/keys).
    -   **Logfire Token (Optional)**: For observability.

## Setup

1.  **Clone the repository and navigate into it.**

2.  **Set up the Database:**
    Create a `docker-compose.yml` file in the project root:
    ```yaml
    version: '3.8'
    services:
      postgres:
        image: postgres:16-alpine
        container_name: automarket-db
        environment:
          - POSTGRES_USER=automarket
          - POSTGRES_PASSWORD=automarket
          - POSTGRES_DB=automarket
        ports:
          - "5432:5432"
        volumes:
          - postgres_data:/var/lib/postgresql/data
    volumes:
      postgres_data:
    ```
    Start the database service:
    ```bash
    docker-compose up -d
    ```

3.  **Configure Environment Variables:**
    Copy the example `.env` file and fill in your API key.
    ```bash
    cp .env.example .env
    ```
    Edit `.env` to add your `OPENROUTER_API_KEY`. The database URL is pre-configured for the Docker setup.

4.  **Install Python Dependencies:**
    ```bash
    uv pip install -r requirements.txt
    ```

## Running the Application

### 1. Run the Pydantic AI Backend

In your first terminal, start the FastAPI server:

```bash
uv run uvicorn src.automarket.main:app --reload --reload-dir src
```

The backend server will be running at `http://localhost:8000`. It will automatically create the necessary tables in the PostgreSQL database on startup.

### 2. Run the AG-UI Dojo Frontend

In your second terminal, run the AG-UI Dojo:

1.  **Clone the AG-UI repository (if you haven't already):**
    ```bash
    git clone https://github.com/ag-ui-protocol/ag-ui.git
    ```

2.  **Navigate to the Dojo app and run it:**
    ```bash
    cd ag-ui/typescript-sdk
    deno task dojo
    ```

### 3. Interact with AutoMarket

1.  Open your browser to the AG-UI Dojo: **[http://localhost:3000](http://localhost:3000)**.
2.  In the "Custom Agent" input box, enter your backend URL: `http://localhost:8000`.
3.  Click "Connect".
4.  Paste a conversation transcript into the chat to start the process. The agent will guide you through the steps.