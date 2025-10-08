from sqlalchemy import create_engine
import pandas as pd
from pathlib import Path

DB_PATH = "data/retail.db"           # where the SQLite file lives
DATA_DIR = Path("data/real")         # where your CSVs are stored

# Map CSV file names → target table names
FILES = {
    "customers.csv": "customers",
    "products.csv": "products",
    "orders.csv": "orders",
    "order_items.csv": "order_items",
}

# Friendly dtype coercions so SQLite types are predictable
DTYPES = {
    "customers": {"customer_id": "Int64", "name": "string", "city": "string", "join_date": "string"},
    "products":  {"product_id": "Int64", "name": "string", "category": "string", "price": "float64"},
    "orders":    {"order_id": "Int64", "customer_id": "Int64", "order_date": "string"},
    "order_items": {"order_item_id": "Int64", "order_id": "Int64", "product_id": "Int64", "quantity": "Int64"},
}

def main():
    engine = create_engine(f"sqlite:///{DB_PATH}")
    with engine.begin() as conn:
        
        # 1) turn off FKs to make dropping/reloading tables simple & atomic
        conn.exec_driver_sql("PRAGMA foreign_keys = OFF;")
        
        # 2) drop existing tables so the load is repeatable
        for t in ["order_items","orders","products","customers"]:
            conn.exec_driver_sql(f"DROP TABLE IF EXISTS {t};")
        
        # 3) load every CSV into its table
        for fname, table in FILES.items():
            fp = DATA_DIR / fname
            df = pd.read_csv(fp)
            
            # Coerce dtypes for stable schema
            if table in DTYPES:
                for col, dt in DTYPES[table].items():
                    if col in df.columns:
                        if dt.startswith("Int"):
                            df[col] = pd.to_numeric(df[col], errors="coerce").astype(dt)
                        elif dt == "float64":
                            df[col] = pd.to_numeric(df[col], errors="coerce")
                        else:
                            df[col] = df[col].astype(dt)

            # Write to SQLite; pandas creates/overwrites the table
            df.to_sql(table, con=conn, if_exists="replace", index=False)
            print(f"✅ loaded {len(df):,} rows into {table}")

        # 4) helpful indexes (ignore if they fail)
        try:
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);")
            conn.exec_driver_sql("CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);")
        except Exception:
            pass
        
        # 5) re-enable FKs for future queries (good hygiene)
        conn.exec_driver_sql("PRAGMA foreign_keys = ON;")

    print(f"🎉 Data loaded into {DB_PATH}")

if __name__ == "__main__":
    main()
