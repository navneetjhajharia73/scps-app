import os
import httpx
from jose import jwt, JWTError
from fastapi import HTTPException, Request

# ============================================================
# SSO Authentication — Okta, Auth0, PingID support
# Env vars Snowflake Secrets se aayenge
# ============================================================

SSO_PROVIDER = os.getenv("SSO_PROVIDER", "auth0")
CLIENT_ID = os.getenv("SSO_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("SSO_CLIENT_SECRET", "")
ISSUER_URL = os.getenv("SSO_ISSUER_URL", "")
REDIRECT_URI = os.getenv("SSO_REDIRECT_URI", "")


def get_endpoints():
    provider = SSO_PROVIDER.lower()

    if "okta" in provider:
        return {
            "authorize": f"{ISSUER_URL}/v1/authorize",
            "token": f"{ISSUER_URL}/v1/token",
            "jwks": f"{ISSUER_URL}/v1/keys",
            "userinfo": f"{ISSUER_URL}/v1/userinfo",
        }
    elif "auth0" in provider:
        return {
            "authorize": f"{ISSUER_URL}/authorize",
            "token": f"{ISSUER_URL}/oauth/token",
            "jwks": f"{ISSUER_URL}/.well-known/jwks.json",
            "userinfo": f"{ISSUER_URL}/userinfo",
        }
    elif "ping" in provider:
        return {
            "authorize": f"{ISSUER_URL}/as/authorization.oauth2",
            "token": f"{ISSUER_URL}/as/token.oauth2",
            "jwks": f"{ISSUER_URL}/pf/JWKS",
            "userinfo": f"{ISSUER_URL}/idp/userinfo.openid",
        }
    else:
        return {
            "authorize": f"{ISSUER_URL}/authorize",
            "token": f"{ISSUER_URL}/token",
            "jwks": f"{ISSUER_URL}/.well-known/jwks.json",
            "userinfo": f"{ISSUER_URL}/userinfo",
        }


ENDPOINTS = get_endpoints()
AUTHORIZE_URL = ENDPOINTS["authorize"]
TOKEN_URL = ENDPOINTS["token"]
JWKS_URL = ENDPOINTS["jwks"]
USERINFO_URL = ENDPOINTS["userinfo"]


def get_login_url():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": "openid profile email",
        "redirect_uri": REDIRECT_URI,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{AUTHORIZE_URL}?{query}"


async def exchange_code_for_token(code: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail=f"Token exchange failed: {response.text}")

    return response.json()


async def get_jwks():
    async with httpx.AsyncClient() as client:
        response = await client.get(JWKS_URL)
    return response.json()


async def verify_token(token: str):
    try:
        jwks = await get_jwks()

        # Auth0 ke liye audience alag hota hai
        provider = SSO_PROVIDER.lower()
        if "auth0" in provider:
            audience = f"{ISSUER_URL}/api/v2/"
            issuer = f"{ISSUER_URL}/"
        else:
            audience = CLIENT_ID
            issuer = ISSUER_URL

        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            options={"verify_aud": False},  # Auth0 id_token mein aud = client_id
        )
        return payload
    except JWTError:
        # Token verify nahi hua — userinfo endpoint se try karo
        return await get_userinfo(token)


async def get_userinfo(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {token}"},
        )

    if response.status_code != 200:
        raise HTTPException(status_code=401, detail="Token invalid")

    return response.json()


async def get_current_user(request: Request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = auth_header.split(" ")[1]
    user = await verify_token(token)

    return {
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "sub": user.get("sub", ""),
    }