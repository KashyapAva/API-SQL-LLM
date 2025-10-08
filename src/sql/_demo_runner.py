from src.sql.runner import run_sql_safe

# Try a safe SELECT
cols, rows = run_sql_safe("""
SELECT name, city FROM customers ORDER BY name ASC;
""")
print("COLUMNS:", cols)
print("ROWS:", rows)

# Try a blocked statement (should raise ValueError)
try:
    run_sql_safe("DROP TABLE customers;")
except Exception as e:
    print("BLOCKED as expected:", e)
