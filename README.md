# Text-to-SQL LLM Copilot (FastAPI + SQLite)

Turn natural language questions into safe SQL over your data.  
Built with FastAPI, SQLAlchemy, **sqlglot** guardrails, and an optional OpenAI LLM.

## ✨ Features
- **Text → SQL**: Rule-based baseline or LLM (OpenAI) with few-shots
- **Safety**: Read-only enforcement via `sqlglot` (blocks DROP/UPDATE/DELETE/DDL)
- **Dynamic schema**: LLM sees your actual SQLite tables/columns at runtime
- **All-click VS Code workflow**: Run, seed/load, and test via launch configs—no bash

## 🧩 Repo Structure
src/
    api/    app.py # FastAPI app (/health, /query)
    core/   config.py # Settings (.env via python-dotenv)
    db/ 
        seed_db.py # Small demo seed
        load_csvs.py # Load real CSVs -> SQLite
    nlp/    pipeline.py # Baseline & LLM SQL generators
    sql/    runner.py # Validate+run SQL safely (sqlglot)
.vscode/launch.json # Click-to-run configs
requirements.txt


## 🚀 Quickstart (VS Code only)
1. Create `.env` in project root:

OPENAI_API_KEY=sk-... # optional (only if using LLM)
MODEL_PROVIDER=openai
MODEL_NAME=gpt-4o-mini
USE_LLM=true

2. **Install deps** (VS Code → Python: Manage Packages) or right-click `requirements.txt` → *Install All*.
3. (Optional) Load your CSVs  
- Put `customers.csv`, `products.csv`, `orders.csv`, `order_items.csv` into `data/real/`  
- Run **Load real CSVs** (module: `src.db.load_csvs`)
4. Start API: **Start FastAPI (Uvicorn)** → open http://localhost:8000/docs
5. Try **POST /query**:
```json
{ "question": "revenue by category in 2024", "limit": 10 }