import os
import duckdb
from dotenv import load_dotenv

# Charge .env
load_dotenv()

MY_BUCKET = os.getenv("MY_BUCKET")
CHEMIN_PARQUET = os.getenv("CHEMIN_PARQUET")


con = duckdb.connect(database=":memory:")

query_definition = f"SELECT * FROM read_parquet('s3://{MY_BUCKET}/{CHEMIN_PARQUET}')"
df = con.sql(query_definition)

print(df)
# # Si ça marche, tu peux ensuite écrire le parquet
# con.execute(f"""
#     COPY (
#         SELECT * 
#         FROM read_csv('s3://{MY_BUCKET}/{CHEMIN_PARQUET}')
#     ) 
#     TO 's3://{MY_BUCKET}/{OUTPUT_PATH}' 
#     (FORMAT PARQUET)
# """)