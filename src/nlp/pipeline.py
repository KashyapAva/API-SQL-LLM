# this script turns a natural language question into a safe SQL query that runner.py will execute.

from sqlalchemy import create_engine, text
from src.core.config import get_settings

def _list_tables_sqlite():
    engine = create_engine(f"sqlite:///{get_settings().sqlite_path}")
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")).fetchall()
    return [r[0] for r in rows]

def _columns_sqlite(table: str):
    engine = create_engine(f"sqlite:///{get_settings().sqlite_path}")
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({table});")).fetchall()
    return [(r[1], r[2]) for r in rows]  # (name, type)

def get_schema_summary() -> str:
    lines = []
    for t in _list_tables_sqlite():
        cols = _columns_sqlite(t)
        sig = ", ".join(f"{c} {typ or ''}".strip() for c, typ in cols)
        lines.append(f"TABLE {t} ({sig})")
    return "\n".join(lines)



# re - regular expressions, generalized strings sort of
# You use the regular expression (regex) module to extract patterns like years (e.g., 2024) from text.
import re

def _year_from_text(text: str):
    
    # re.search() - scans the entire string for the first occurance of a match
    # Looks for a 4-digit number starting with 19 or 20 (matches years like 1999, 2024).
    # If found, returns the year as a string; otherwise returns None.
    
    m = re.search(r"(19|20)\d{2}", text)
    return m.group(0) if m else None

def _intent_from_text(text: str):
    
    # Converts text to lowercase
    t = text.lower()
    
    # Checks for simple keyword patterns. Maps them to a short “intent name”.
    if "top" in t and "customer" in t:
        return "top_customers_by_spend"
    if ("revenue" in t or "sales" in t) and ("by product" in t or "per product" in t):
        return "revenue_by_product"
    if "orders" in t and "by" in t and "customer" in t:
        return "orders_by_customer"
    if "average order value" in t or "aov" in t:
        return "avg_order_value"
    if "daily sales" in t or ("sales" in t and "by day" in t):
        return "daily_sales"
    
    # if none of them match then fallback search
    return "fallback_search"

def _date_filters(year: str | None):
    # If a year exists, returns an SQL snippet to filter rows by that year. If no year is found, returns an empty string.
    if not year:
        return ""
    # filters Orders table by year
    return f" AND strftime('%Y', o.order_date) = '{year}' "

def generate_sql(question: str, limit: int | None = 10) -> str:
    """
    Simple keyword→template baseline that returns safe, read-only SQL for our schema.
    """
    intent = _intent_from_text(question)
    year = _year_from_text(question)
    
    # Builds a LIMIT clause string only if the user asked for one.
    lim = f" LIMIT {limit} " if limit else ""

    if intent == "top_customers_by_spend":
        return f"""
        SELECT c.name AS customer, ROUND(SUM(oi.quantity * p.price), 2) AS total_spend
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        
        WHERE 1=1 {_date_filters(year)}
        GROUP BY c.customer_id
        ORDER BY total_spend DESC
        {lim};
        """

    if intent == "revenue_by_product":
        return f"""
        SELECT p.name AS product, ROUND(SUM(oi.quantity * p.price), 2) AS revenue
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE 1=1 {_date_filters(year)}
        GROUP BY p.product_id
        ORDER BY revenue DESC
        {lim};
        """

    if intent == "orders_by_customer":
        return f"""
        SELECT c.name AS customer, COUNT(DISTINCT o.order_id) AS orders
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE 1=1 {_date_filters(year)}
        GROUP BY c.customer_id
        ORDER BY orders DESC
        {lim};
        """

    if intent == "avg_order_value":
        return f"""
        SELECT ROUND(AVG(basket_total), 2) AS avg_order_value
        FROM (
            SELECT o.order_id, SUM(oi.quantity * p.price) AS basket_total
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE 1=1 {_date_filters(year)}
            GROUP BY o.order_id
        ) t
        {lim};
        """

    if intent == "daily_sales":
        return f"""
        SELECT o.order_date AS day, ROUND(SUM(oi.quantity * p.price), 2) AS revenue
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE 1=1 {_date_filters(year)}
        GROUP BY o.order_date
        ORDER BY o.order_date ASC
        {lim};
        """

    # fallback: show top orders by basket size
    # If nothing matches, it gives a generic “top orders by total value” query.
    return f"""
    SELECT o.order_id, c.name AS customer, o.order_date, SUM(oi.quantity * p.price) AS total
    FROM orders o
    JOIN customers c ON o.customer_id = c.customer_id
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    GROUP BY o.order_id, c.name, o.order_date
    ORDER BY total DESC
    {lim};
    """


# Appending the LLM Integrerated code

# --- LLM integration (OpenAI) ---

import os                        # read environment variables
from textwrap import dedent      # clean multi-line string indentation
try:
    from openai import OpenAI    # OpenAI client (v1+)
except Exception:
    OpenAI = None                # graceful fallback if package missing

# Gives the model the exact tables/columns it’s allowed to use. Important: keeps the model “on rails” for SQLite.

SCHEMA_DDL = dedent("""
CREATE TABLE customers (
  customer_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT,
  join_date TEXT
);
CREATE TABLE products (
  product_id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT,
  price REAL NOT NULL
);
CREATE TABLE orders (
  order_id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  order_date TEXT NOT NULL
);
CREATE TABLE order_items (
  order_item_id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL
);
""").strip()

# steer the model, Concrete Q→SQL pairs nudge the model toward your style and correct joins.
FEW_SHOTS = [
    {
        "q": "top 5 customers by total spend",
        "sql": """
SELECT c.name AS customer, ROUND(SUM(oi.quantity * p.price), 2) AS total_spend
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY c.customer_id
ORDER BY total_spend DESC
LIMIT 5;
""".strip()
    },
    {
        "q": "total revenue by product in 2024",
        "sql": """
SELECT p.name AS product, ROUND(SUM(oi.quantity * p.price), 2) AS revenue
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE strftime('%Y', o.order_date) = '2024'
GROUP BY p.product_id
ORDER BY revenue DESC;
""".strip()
    },
    {
        "q": "revenue by category in 2024",
        "sql": """
SELECT p.category AS category, ROUND(SUM(oi.quantity * p.price), 2) AS revenue
FROM order_items oi
JOIN orders o   ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE strftime('%Y', o.order_date) = '2024'
GROUP BY p.category
ORDER BY revenue DESC
LIMIT 10;
""".strip()
}
]

# Hard constraints to prevent unsafe / irrelevant SQL. Tells the model to output SQL only (no explanations).

# modified prompt where instead of a defined set of guidelines for the data, it gets it automatically (generalized).
    
def _system_prompt():
    schema_text = get_schema_summary()
    return f"""
You are a SQLite SQL assistant. Return ONLY a valid SQL query — no comments, no prose, no markdown.
Rules:
- The output must start with SELECT or WITH (or PRAGMA).
- Use ONLY the listed tables/columns; do not invent columns.
- Read-only only: no INSERT/UPDATE/DELETE/DDL.
- If the question says "by X", include X in SELECT and GROUP BY.
- If no limit is specified, add a reasonable LIMIT.
Schema:
{schema_text}
""".strip()


# Concatenates examples in a readable “Q: … / SQL: …” format.
def _fewshot_block():
    blocks = []
    for ex in FEW_SHOTS:
        blocks.append(f"Q: {ex['q']}\nSQL:\n{ex['sql']}")
    return "\n\n".join(blocks)

# Removes code fences if the model adds them; ensures a trailing semicolon—helpful for SQLite.
def _clean_sql(s: str) -> str:
    s = s.strip()
    # remove code fences if the model added them
    if s.startswith("```"):
        s = s.strip("`")
        # drop leading 'sql' if present
        s = s.replace("sql\n", "", 1).replace("SQL\n", "", 1)
    # ensure it ends with a semicolon for SQLite
    if not s.endswith(";"):
        s += ";"
    return s

# Validates prerequisites (package + key).
# Builds a message stack: system rules → few-shots → your question.
# Calls the Chat Completions API with temperature=0 (deterministic).
# Cleans the returned text and hands a pure SQL string back.

from src.core.config import get_settings

def generate_sql_with_llm(question: str, limit: int | None = 10) -> str:
    """
    Call the LLM to synthesize SQL, constrained by schema and instructions.
    Falls back with a helpful error if openai package/key is missing.
    """
    
    settings = get_settings()
    
    if OpenAI is None:
        raise RuntimeError("openai package not installed. Install 'openai' in your venv.")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Put it in your .env.")
    
    client = OpenAI(api_key=settings.openai_api_key)
    model_name = settings.llm_model or "gpt-4o-mini"
    user_msg = f"Question: {question}\nReturn only SQL. If appropriate, include LIMIT {limit or 10}."

    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": _fewshot_block()},
        {"role": "user", "content": user_msg},
    ]

    # Using Chat Completions
    resp = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0,
    )
    sql = resp.choices[0].message.content
    return _clean_sql(sql or "")



# Effect on logic: you now have two SQL generators:

# generate_sql(...) → deterministic rule-based baseline (what you wrote earlier)

# generate_sql_with_llm(...) → schema-constrained model-generated SQL

# You can A/B them and compare results.