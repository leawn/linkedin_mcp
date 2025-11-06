# Restack AI - LinkedIn MCP

This repository contains a LinkedIn MCP based on Restack.

## Prerequisites

- Docker (for running Restack)
- Python 3.10 or higher
- A Restack account (for cloud deployment)
- API keys for BrightData and/or Phantombuster

## Environment Variables

Create a `.env` file in the root of the project. All required environment variables are listed in the `env.example` file.

## Start Restack

To start Restack locally, use the following Docker command:

```bash
docker run -d --pull always --name restack -p 5233:5233 -p 6233:6233 -p 7233:7233 -p 9233:9233 -p 10233:10233 ghcr.io/restackio/restack:main
```

## Setup Python Environment

Create and activate a virtual environment.

If using uv:
```bash
uv venv && source .venv/bin/activate
```

If using pip:
```bash
python -m venv .venv && source .venv/bin/activate
```

## Install dependencies

If using uv:
```bash
uv sync
```

If using pip:
```bash
pip install -r requirements.txt
pip install -e .
```

## Run services

This will start the Restack services and connect to the engine.

If using uv:
```bash
uv run dev
```

If using pip:
```bash
python -c "from src.services import watch_services; watch_services()"
```

## Available Workflows

This MCP provides several workflows to interact with LinkedIn:

### BrightData
- `GetLinkedinProfileWorkflowBrightdata`: Get a LinkedIn profile.
- `GetLinkedinProfilePostsWorkflowBrightdata`: Get posts from a LinkedIn profile.
- `GetLinkedinProfileReactionsWorkflowBrightdata`: Get reactions on posts from a LinkedIn profile.

### Phantombuster
- `GetLinkedinProfileWorkflowPhantombuster`: Get a LinkedIn profile.
- `GetLinkedinProfilePostsWorkflowPhantombuster`: Get posts from a LinkedIn profile.
- `GetLinkedinProfileReactionsWorkflowPhantombuster`: Get reactions on posts from a LinkedIn profile.
- `SaveLinkedinLeadWorkflowPhantombuster`: Save a LinkedIn profile as a lead.

### LinkedIn
- `CreatePostOnLinkedinWorkflow`: Create a post on LinkedIn.

You can trigger these workflows from the Restack UI or API.

## Deploy on Restack Cloud

To deploy the application on Restack, you can create an account at [https://console.restack.io](https://console.restack.io) and follow the documentation to deploy your agent.
