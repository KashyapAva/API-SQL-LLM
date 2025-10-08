from src.nlp.pipeline import generate_sql
from src.sql.runner import run_sql_safe

q = "total revenue by product in 2024"
sql = generate_sql(q, limit=10)
print("SQL:\n", sql)

cols, rows = run_sql_safe(sql)
print("COLUMNS:", cols)
print("ROWS:", rows)