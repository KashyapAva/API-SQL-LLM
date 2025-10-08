# This wraps your logic into an HTTP API so you can call it from a web client or Swagger UI.

# FastAPI → framework to create API endpoints.
# HTTPException → used to return errors (like invalid SQL).
# BaseModel and Field → define and validate request/response data shapes.
# generate_sql() and run_sql_safe() → your core logic.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from src.nlp.pipeline import generate_sql, generate_sql_with_llm
from src.core.config import get_settings
from src.sql.runner import run_sql_safe

# Creates a FastAPI instance. The title appears in the Swagger UI.
app = FastAPI(title="Text-to-SQL Analytics Copilot")

# defining the request
class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question")
    limit: int | None = Field(default=10, ge=1, le=100)

# defines the structure of the response
class QueryResponse(BaseModel):
    sql: str
    rows: list[list] | None = None
    columns: list[str] | None = None

# Simple GET endpoint to confirm the API is up. Useful for deployment health checks.
@app.get("/health")
def health():
    return {"status": "ok"}

# Generate SQL, Run it safely, Return a structured JSON with SQL, rows, and columns.
# If anything goes wrong (e.g., unsafe SQL, parsing error), it raises an HTTP 400 error with the reason.
@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    settings = get_settings()
    print(f"[DEBUG] use_llm={settings.use_llm}, model={settings.llm_model}, provider={settings.llm_provider}")
    try:
        if settings.use_llm:                                             # ← feature flag
            sql = generate_sql_with_llm(req.question, limit=req.limit)
        else:
            sql = generate_sql(req.question, limit=req.limit)

        cols, rows = run_sql_safe(sql)                                  # ← guardrails still apply
        return QueryResponse(sql=sql, rows=rows, columns=cols)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

from src.core.config import get_settings