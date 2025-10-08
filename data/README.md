# Data folder

This project runs on SQLite (`data/retail.db`).  
To load your own CSVs:

1) Put `customers.csv`, `products.csv`, `orders.csv`, `order_items.csv` into `data/real/`.  
2) In VS Code → Run & Debug → **Load real CSVs** (module: `src.db.load_csvs`).  
3) Start the API → **Start FastAPI (Uvicorn)** → open http://localhost:8000/docs