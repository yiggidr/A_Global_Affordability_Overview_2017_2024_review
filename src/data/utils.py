import os
import duckdb
from dotenv import load_dotenv


def configure_s3(con: duckdb.DuckDBPyRelation):
    load_dotenv()
    # s3_endpoint = os.getenv("AWS_S3_ENDPOINT", "minio.lab.sspcloud.fr").replace(
    #     "https://", ""
    # )

    # con.execute("INSTALL httpfs; LOAD httpfs;")
    # con.execute(f"SET s3_endpoint='{s3_endpoint}';")
    con.execute(f"SET s3_access_key_id='{os.getenv('AWS_ACCESS_KEY_ID')}';")
    con.execute(f"SET s3_secret_access_key='{os.getenv('AWS_SECRET_ACCESS_KEY')}';")
    con.execute("SET s3_url_style='path';")

    if os.getenv("AWS_SESSION_TOKEN"):
        con.execute(f"SET s3_session_token='{os.getenv('AWS_SESSION_TOKEN')}';")
