# portal_ldap
#
# Contains LDAP operations needed for the portal. Included here in a separate
# file to make them easier to use from an interactive session.

import ldap
import ldap.modlist
import kinds
import datetime


def connect(ldap_url, ldap_user, ldap_password):
    conn = ldap.initialize(ldap_url)
    conn.set_option(ldap.OPT_REFERRALS, 0)
    conn.simple_bind_s(ldap_user, ldap_password)
    return conn


def get_user_dn(conn, base_dn, username: str):
    search_filter = f"(&(objectClass=person)(uid={username}))"
    result = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter)
    retval = ""
    if result and result[0]:
        retval = result[0][0]
    return retval


default_group_attrlist = [
    "objectClass",
    "displayName",
    "sambaGroupType",
    "sambaSID",
    "gidNumber",
    "cn",
    "description",
]


def days_since_epoch():
    epoch = datetime.datetime.fromtimestamp(0, datetime.UTC)
    today = datetime.datetime.now(datetime.UTC)
    diff = today - epoch
    return diff.days


# Returns a list of tuples of the format: (dn, attribute map). The attribute map contains
# key-value pairs with the keys coming from the attrlist parameter. The attrlist
# parameter excludes the memberUid attribute because it's likely to be a huge list of
# usernames and retrieving them all is an expensive operation.
def get_user_groups(
    conn,
    base_dn,
    username: str,
    attrlist=default_group_attrlist,
):
    search_filter = f"(&(objectClass=posixGroup)(memberUid={username}))"
    result = conn.search_s(
        base_dn, ldap.SCOPE_SUBTREE, search_filter, attrlist=attrlist
    )
    return result


def get_groups(
    conn,
    base_dn,
    attrlist=default_group_attrlist,
):
    search_filter = "(&(objectClass=posixGroup))"
    return conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, attrlist=attrlist)


def get_user(conn, base_dn, username: str):
    search_filter = f"(&(objectClass=posixAccount)(uid={username}))"
    return conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter)


def create_user(conn, base_dn, days_since_epoch, user: kinds.CreateUserRequest):
    new_user = ldap.modlist.addModlist(
        {
            "objectClass": [b"posixAccount", b"shadowAccount", b"inetOrgPerson"],
            "givenName": user.first_name.encode("UTF-8"),
            "sn": user.last_name.encode("UTF-8"),
            "cn": f"{user.first_name} {user.last_name}".encode("UTF-8"),
            "uid": user.username.encode("UTF-8"),
            "userPassword": user.password.encode("UTF-8"),
            "mail": user.email.encode("UTF-8"),
            "departmentNumber": user.department.encode("UTF-8"),
            "o": user.organization.encode("UTF-8"),
            "title": user.title.encode("UTF-8"),
            "homeDirectory": f"/home/{user.username}".encode("UTF-8"),
            "loginShell": b"/bin/bash",
            "gidNumber": b"10013",
            "uidNumber": user.user_uid.encode("UTF-8"),
            "shadowLastChange": days_since_epoch.encode("UTF-8"),
            "shadowMin": b"1",
            "shadowMax": b"730",
            "shadowInactive": b"10",
            "shadowWarning": b"10",
        }
    )
    return conn.add_s(f"uid={user.username},ou=People,{base_dn}", new_user)


def add_user_to_group(conn, base_dn, username, group):
    mod_group = [
        (
            ldap.MOD_ADD,
            "memberUid",
            [username.encode("UTF-8")],
        )
    ]
    return conn.modify_s(
        f"cn={group},ou=Groups,{base_dn}",
        mod_group,
    )


def delete_user(conn, base_dn, username):
    return conn.delete_s(
        f"uid={username},ou=People,{base_dn}",
    )


def change_password(conn, base_dn, username, password):
    return conn.passwd_s(f"uid={username},ou=People,{base_dn}", None, password)


def shadow_last_change(conn, base_dn, days_since_epoch, username):
    mod_shadow = [
        (
            ldap.MOD_DELETE,
            "shadowLastChange",
            None,
        ),
        (
            ldap.MOD_ADD,
            "shadowLastChange",
            [days_since_epoch.encode("UTF-8")],
        ),
    ]
    return conn.modify_s(
        f"uid={username},ou=People,{base_dn}",
        mod_shadow,
    )
