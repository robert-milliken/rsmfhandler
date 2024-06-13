# Azure Functions Project

## Introduction

This project uses Azure Functions to process and summarize messages based on different time intervals (week, month, or custom intervals). It involves handling requests via HTTP triggers, grouping messages, and interacting with an AI language model to generate concise summaries.

## Features

- **HTTP Trigger:** Process requests sent to the Azure Function via HTTP.
- **Message Grouping:** Group messages by week, month, or a specified number of days.
- **AI Summarization:** Utilize an AI model to summarize grouped messages into a structured format.
- **SSL Configuration:** Option to allow self-signed HTTPS certificates for development purposes.

## Requirements

- Azure Functions Core Tools
- Python 3.8 or higher
- An active Azure subscription
- Access to an AI language model API

## Usage

Send a POST request to the function's HTTP endpoint with the necessary parameters:

- **prompt:** The summarization prompt for the AI.
- **interval:** The interval to group messages (week, month, or number of days).
- **rsmf:** JSON object containing the messages.
- **temp:** The temperature setting for the AI model.

### Example Request:

```bash
curl -X POST http://localhost:7071/api/http_trigger -H "Content-Type: application/json" -d '
{
    "prompt": "Summarize the messages",
    "interval": "week",
    "rsmf": {"messages": [...]},
    "temp": "0.5"
}'
```

### Licence
MIT License