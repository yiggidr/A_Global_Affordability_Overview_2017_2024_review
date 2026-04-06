import duckdb

def get_connection():
    con = duckdb.connect("diet.duckdb")
    con.execute("""
        CREATE OR REPLACE TABLE diet AS
        SELECT * FROM 'data/price_of_healthy_diet_clean.csv'
    """)
    return con
