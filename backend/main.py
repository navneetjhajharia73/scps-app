import os
import snowflake.connector
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SPCS App Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_login_token():
    """
    SPCS container ke andar Snowflake automatically ek OAuth token
    file rakhta hai: /snowflake/session/token
    Ye token har kuch minutes mein auto-refresh hota hai.
    Isse padh ke Snowflake se connect karte hain — koi password nahi.
    """
    try:
        with open('/snowflake/session/token', 'r') as f:
            return f.read()
    except FileNotFoundError:
        # Local testing mein ye file nahi hogi
        return None


def get_snowflake_connection():
    """
    2 modes mein kaam karta hai:
    1. SPCS mein: auto token + SNOWFLAKE_HOST se connect (koi password nahi)
    2. Local mein: password se connect (testing ke liye)
    """
    token = get_login_token()

    if token:
        # ---- SPCS MODE ----
        # SNOWFLAKE_ACCOUNT aur SNOWFLAKE_HOST Snowflake auto inject karta hai
        # SNOWFLAKE_WAREHOUSE, DATABASE, SCHEMA secrets se aate hain
        return snowflake.connector.connect(
            host=os.getenv('SNOWFLAKE_HOST'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            token=token,
            authenticator='oauth',
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
            database=os.getenv('SNOWFLAKE_DATABASE'),
            schema=os.getenv('SNOWFLAKE_SCHEMA'),
        )
    else:
        # ---- LOCAL MODE ----
        # Local testing ke liye password se connect
        # .env file ya export se set karo
        return snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT', ''),
            user=os.getenv('SNOWFLAKE_USER', ''),
            password=os.getenv('SNOWFLAKE_PASSWORD', ''),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', ''),
            database=os.getenv('SNOWFLAKE_DATABASE', ''),
            schema=os.getenv('SNOWFLAKE_SCHEMA', ''),
        )


@app.get("/health")
def health():
    """
    Basic health check.
    SPCS ka readiness probe ye hit karta hai.
    Jab tak 200 nahi milta, service ko traffic nahi jayega.
    """
    return {"status": "healthy"}


@app.get("/health/db")
def health_db():
    """Snowflake se connection theek hai ya nahi"""
    try:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        cur.execute("SELECT CURRENT_TIMESTAMP()")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"status": "connected", "snowflake_time": str(result[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB connection failed: {e}")


@app.get("/api/query")
def run_query(table: str = "SAMPLE_TABLE", limit: int = 10):
    """Kisi table se data fetch karo"""
    try:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        safe_table = table.replace('"', '""')
        cur.execute(f'SELECT * FROM "{safe_table}" LIMIT %s', (limit,))
        columns = [desc[0] for desc in cur.description]
        rows = [dict(zip(columns, row)) for row in cur.fetchall()]
        cur.close()
        conn.close()
        return {"columns": columns, "rows": rows, "count": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tables")
def list_tables():
    """Database mein available tables ki list"""
    try:
        conn = get_snowflake_connection()
        cur = conn.cursor()
        cur.execute("SHOW TABLES")
        tables = [row[1] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))