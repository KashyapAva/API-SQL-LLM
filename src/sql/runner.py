# sqlalchemy.create_engine → opens a connection to the SQLite database.
# sqlalchemy.text → wraps a raw SQL string safely for execution.
# sqlglot → parses SQL into a syntax tree so we can inspect and validate it.
# get_settings() → reads the sqlite_path from your config file so the runner knows which database to use.

from sqlalchemy import create_engine, text
import sqlglot
from sqlglot import expressions as exp
from src.core.config import get_settings

# Allow only read-only top-level statements. Everything else will be rejected.
# We only want to execute safe queries — no DELETE, UPDATE, or DROP.
# This set lists the top-level SQL statements that are allowed:
# SELECT – read data
# WITH – read data using common table expressions
# PRAGMA – safe SQLite metadata queries



def _validate_sql(sql: str) -> None:
    """
    Parse the SQL with sqlglot and ensure the top-level statement is read-only.
    Raise ValueError if it's not safe.
    """
    
    try:
        parsed: exp = sqlglot.parse_one(sql, read="sqlite") # parses SQL into abstract syntax tree (AST)
    except Exception as e:
        raise ValueError(f"SQL parse error: {e}") # raises error if cant be parsed
    
    # Allow only SELECT / WITH / PRAGMA at the top level
    if not isinstance(parsed, (exp.Select, exp.With, exp.Pragma)):
        raise ValueError(
            f"Only read-only queries are allowed (SELECT/CTE/PRAGMA). Got: {type(parsed).__name__}"
        )

def run_sql_safe(sql: str):
    """
    Validate then execute the SQL against our SQLite DB.
    Returns: (columns: list[str], rows: list[list])
    """
    
    # This is the main entry point other parts of your app (like the API) will use.
    
    _validate_sql(sql) # validates it according to the function above

    # gets the settings from config.py
    settings = get_settings()
    
    # opens a connection to the database
    engine = create_engine(f"sqlite:///{settings.sqlite_path}")

    with engine.connect() as conn: # opens a connection
        
        # executes the sql safely
        result = conn.execute(text(sql))
        
        # grabs all the returned rows
        rows = result.fetchall()
        
        # gets column names from result
        cols = list(result.keys())

    # Convert Row objects to plain lists for easy JSON serialization
    
    # Converts the SQLAlchemy Row objects into plain Python lists (JSON-friendly).
    # Returns a tuple (columns, rows) that higher layers (like your API) can easily serialize into a response.
    
    return cols, [list(r) for r in rows]


# Overall flow of the script:

# Input SqL string, parse and approve it, connect to db, execute safely, fetch data, return lists for JSON.
