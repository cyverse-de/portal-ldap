from ldap import LDAPError

import portal_ldap
import kinds
import os

from fastapi import FastAPI, HTTPException, status

app = FastAPI()

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
    try:
        portal_ldap.create_user(ldap_conn, ldap_base_dn, dse, user)
    except LDAPError as err:
        raise HTTPException(
            status_code=400, detail=f"desc: '{err.desc}', info: '{err.info}'"
        )
    return {"user": user.username}


@app.post("/groups/{group_name}", status_code=200)
def add_user_to_group(group_name: str, user_info: kinds.SimpleUser):
    try:
        portal_ldap.add_user_to_group(
            ldap_conn, ldap_base_dn, user_info.username, group_name
        )
    except LDAPError as err:
        raise HTTPException(
            status_code=400, detail=f"desc: '{err.desc}', info: '{err.info}'"
        )
    return {"group" : group_name, "user" : user_info.username}


@app.delete("/users/{username}")
def delete_user(username: str):
    try:
        portal_ldap.delete_user(ldap_conn, ldap_base_dn, username)
    except LDAPError as err:
        raise HTTPException(
            status_code=400, detail=f"desc: '{err.desc}', info: '{err.info}'"
        )
    return {"user": username}


@app.put("/users/{username}/password", status_code=200)
def change_password(username: str, password: kinds.SimplePassword):
    try:
        portal_ldap.change_password(
            ldap_conn, ldap_base_dn, username, password.password
        )
    except LDAPError as err:
        raise HTTPException(
            status_code=400, detail=f"desc: '{err.desc}', info: '{err.info}'"
        )
    return {"user": username}


@app.post("/users/{user_id}/shadow-last-change")
def shadow_last_change(user_id: str):
    dse = f"{portal_ldap.days_since_epoch()}"
    try:
        portal_ldap.shadow_last_change(ldap_conn, ldap_base_dn, dse, user_id)
    except LDAPError as err:
        raise HTTPException(
            status_code=400, detail=f"desc: '{err.desc}', info: '{err.info}'"
        )
    return {"user" : user_id}
