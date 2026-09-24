import os
import snowflake.connector
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from auth import get_current_user, get_login_url, exchange_code_for_token

app = FastAPI(title="SPCS App Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Snowflake connection — SPCS auto token se
# ============================================================

def get_login_token():
    try:
        with open('/snowflake/session/token', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return None


def get_snowflake_connection():
    token = get_login_token()
    if token:
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
        return snowflake.connector.connect(
            account=os.getenv('SNOWFLAKE_ACCOUNT', ''),
            user=os.getenv('SNOWFLAKE_USER', ''),
            password=os.getenv('SNOWFLAKE_PASSWORD', ''),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', ''),
            database=os.getenv('SNOWFLAKE_DATABASE', ''),
            schema=os.getenv('SNOWFLAKE_SCHEMA', ''),
        )


# ============================================================
# PUBLIC ROUTES — login ke liye, auth nahi chahiye
# ============================================================

@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/auth/login")
def auth_login():
    return {"login_url": get_login_url()}


@app.get("/auth/callback")
async def auth_callback(code: str):
    tokens = await exchange_code_for_token(code)
    return {
        "access_token": tokens.get("access_token"),
        "id_token": tokens.get("id_token"),
        "token_type": "Bearer",
    }


@app.get("/auth/me")
async def auth_me(user=Depends(get_current_user)):
    return user


# ============================================================
# PROTECTED ROUTES — SSO token chahiye
# ============================================================

@app.get("/health/db")
async def health_db(user=Depends(get_current_user)):
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
async def run_query(table: str = "SAMPLE_TABLE", limit: int = 10, user=Depends(get_current_user)):
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
async def list_tables(user=Depends(get_current_user)):
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