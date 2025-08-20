from ldap import LDAPError

import portal_ldap
import kinds
import os

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel

app = FastAPI()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    print(exc)
    return JSONResponse(
        content={"detail": exc.detail}, status_code=exc.status_code
    )


@app.middleware("http")
async def exception_handling_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print(str(e))
        return JSONResponse(content=str(e), status_code=500)


ldap_url = os.environ.get("LDAP_URL")
ldap_user = os.environ.get("LDAP_USER")
ldap_pass = os.environ.get("LDAP_PASSWORD")
ldap_base_dn = os.environ.get("LDAP_BASE_DN")

ldap_conn = portal_ldap.connect(ldap_url, ldap_user, ldap_pass)


@app.get("/", status_code=201)
def hello():
    return "Hello from portal-ldap."


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(user: kinds.CreateUserRequest):
    dse = f"{portal_ldap.days_since_epoch()}"
    portal_ldap.create_user(ldap_conn, ldap_base_dn, dse, user)
    return {"user": user.username}


@app.get("/users", status_code=200)
def list_users():
    users = portal_ldap.list_users(ldap_conn, ldap_base_dn)
    return {"users": users}


@app.get("/users/{username}", status_code=200)
def get_user(username: str):
    user = portal_ldap.get_user(ldap_conn, ldap_base_dn, username)
    return {"user": user}


@app.get("/users/{username}/groups", status_code=200)
def get_user_groups(username: str):
    groups = portal_ldap.get_user_groups(ldap_conn, ldap_base_dn, username)
    return {"user": username, "groups": groups}


@app.get("/groups", status_code=200)
def list_groups():
    groups = portal_ldap.get_groups(ldap_conn, ldap_base_dn)
    return {"groups": groups}


@app.post("/groups/{group_name}/users/{username}", status_code=200)
def add_user_to_group(group_name: str, username: str):
    portal_ldap.add_user_to_group(ldap_conn, ldap_base_dn, username, group_name)
    return {"group": group_name, "user": username}


@app.delete("/groups/{group}/users/{username}", status_code=200)
def remove_user_from_group(username: str, group: str):
    portal_ldap.remove_user_from_group(ldap_conn, ldap_base_dn, username, group)
    return {"group": group, "username": username}


@app.delete("/users/{username}")
def delete_user(username: str):
    portal_ldap.delete_user(ldap_conn, ldap_base_dn, username)
    return {"user": username}


@app.put("/users/{username}/password", status_code=200)
def change_password(username: str, password: kinds.SimplePassword):
    portal_ldap.change_password(
        ldap_conn, ldap_base_dn, username, password.password
    )
    return {"user": username}


@app.post("/users/{user_id}/shadow-last-change")
def shadow_last_change(user_id: str):
    dse = f"{portal_ldap.days_since_epoch()}"
    portal_ldap.shadow_last_change(ldap_conn, ldap_base_dn, dse, user_id)
    return {"user": user_id}
