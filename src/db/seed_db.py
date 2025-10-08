# create_engine - used to connect to a database using the sqlalchemy library.
from sqlalchemy import create_engine

# defintion of main function
def main():
    # Create the SQLite file inside the data/ folder
    # create engine function will connect it to the SQLite file in the data folder
    engine = create_engine("sqlite:///data/retail.db")
    with engine.begin() as conn:
        # safety for repeatable runs
        
        # This statement will ensure that we dont insert into a child table that references 
        # a non-existent value in the parent tables primary key
        conn.exec_driver_sql("PRAGMA foreign_keys = ON;")
        
        # creating the tables of interest: order_items, orders, products and customers
        conn.exec_driver_sql("DROP TABLE IF EXISTS order_items;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS orders;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS products;")
        conn.exec_driver_sql("DROP TABLE IF EXISTS customers;")

        # schema
        # create the customers table with features and the primary key of customer id
        conn.exec_driver_sql("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT,
            join_date TEXT
        );""")
        
        # create the products table
        conn.exec_driver_sql("""
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price REAL NOT NULL
        );""")

        # create the orders table
        conn.exec_driver_sql("""
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        );""")

        # create the order_items table
        conn.exec_driver_sql("""
        CREATE TABLE order_items (
            order_item_id INTEGER PRIMARY KEY,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            FOREIGN KEY(order_id) REFERENCES orders(order_id),
            FOREIGN KEY(product_id) REFERENCES products(product_id)
        );""")

        # seed rows (keep them small and easy to reason about)
        # the seed rows ensure that reproducible environments and that applications have necessay data to function correctly.
        # can be thought of as intial guides to data parsing or data formatting.
        
        conn.exec_driver_sql("""
        INSERT INTO customers (customer_id, name, city, join_date) VALUES
        (1, 'Alice Johnson', 'Chicago', '2024-01-10'),
        (2, 'Bob Smith', 'Boston', '2024-03-05'),
        (3, 'Carol Lee', 'Austin', '2024-06-20');""")

        conn.exec_driver_sql("""
        INSERT INTO products (product_id, name, category, price) VALUES
        (1, 'Widget A', 'Widgets', 19.99),
        (2, 'Widget B', 'Widgets', 24.99),
        (3, 'Gadget C', 'Gadgets', 49.99),
        (4, 'Gizmo D', 'Gadgets', 99.00);""")

        conn.exec_driver_sql("""
        INSERT INTO orders (order_id, customer_id, order_date) VALUES
        (100, 1, '2024-07-01'),
        (101, 1, '2024-07-15'),
        (102, 2, '2024-08-03'),
        (103, 3, '2024-08-10');""")

        conn.exec_driver_sql("""
        INSERT INTO order_items (order_item_id, order_id, product_id, quantity) VALUES
        (1000, 100, 1, 2),
        (1001, 100, 3, 1),
        (1002, 101, 2, 3),
        (1003, 102, 4, 1),
        (1004, 103, 1, 5);""")

    print("✅ Seeded SQLite DB at data/retail.db")

# that is if the file is run as a script then call main but not when it is imported elsewhere.
if __name__ == "__main__":
    main()
