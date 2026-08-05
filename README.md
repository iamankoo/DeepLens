# 🔍 DeepLens

DeepLens is an AI-powered Deep Research Engine built with FastAPI, LangGraph, and Tavily Search.

It converts a user query into a structured research workflow:

```
User Query
      │
      ▼
Planner Agent
      │
      ▼
Search Agent
      │
      ▼
Source Ranking
      │
      ▼
Writer Agent
      │
      ▼
Structured Research Report
```

---

## 🚀 Features

- FastAPI REST API
- LangGraph Workflow Engine
- Planner Agent
- Search Agent
- Tavily Web Search
- Source Ranking
- Report Generation
- Structured Logging
- Exception Handling
- Modular Architecture

---

## 🏗 Project Structure

```
backend/
│
├── app/
│   ├── agents/
│   ├── api/
│   ├── core/
│   ├── providers/
│   ├── schemas/
│   ├── services/
│   ├── workflows/
│   ├── utils/
│   └── main.py
│
├── requirements.txt
└── .env.example
```

---

## ⚙️ Installation

```bash
git clone <repository-url>

cd DeepLens/backend

pip install -r requirements.txt
```

Create a `.env` file:

```env
TAVILY_API_KEY=YOUR_API_KEY
```

Run the server:

```bash
uvicorn app.main:app --reload
```

Open:

```
http://127.0.0.1:8000/docs
```

---

## 🛠 Tech Stack

- Python
- FastAPI
- LangGraph
- Tavily Search
- Pydantic
- Ruff
- Black

---

## 📌 Current Status

**Version:** `v0.1.0-alpha`

Completed:

- Planning
- Search
- Ranking
- Report Generation

Upcoming:

- LLM Integration
- Memory
- Reflection
- Parallel Execution
- PDF Export
- Multi-Agent Collaboration

---

## 📄 License

MIT License