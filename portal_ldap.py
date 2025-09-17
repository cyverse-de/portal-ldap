# portal_ldap
#
# Contains LDAP operations needed for the portal. Included here in a separate
# file to make them easier to use from an interactive session.

import ldap
import ldap.modlist
import kinds
import datetime


def connect(ldap_url, ldap_user, ldap_password):
    ldap.set_option(ldap.OPT_TIMEOUT, None)

    conn = ldap.ldapobject.ReconnectLDAPObject(
        ldap_url, retry_max=5, retry_delay=3.0
    )
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


def validate_uid_number(user_uid: str) -> int:
    """Validate and convert uidNumber to ensure it's a valid positive integer."""
    try:
        uid_number = int(user_uid)
        if uid_number <= 0:
            raise ValueError(f"uidNumber must be a positive integer, got: {user_uid}")
        return uid_number
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid uidNumber '{user_uid}': must be a positive integer") from e


def validate_shadow_last_change(days_since_epoch) -> int:
    """Validate and convert shadowLastChange to ensure it's a valid non-negative integer."""
    try:
        shadow_last_change = int(days_since_epoch) if isinstance(days_since_epoch, str) else days_since_epoch
        if shadow_last_change < 0:
            raise ValueError(f"shadowLastChange must be non-negative, got: {shadow_last_change}")
        return shadow_last_change
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid shadowLastChange '{days_since_epoch}': must be a non-negative integer") from e


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
    return conn.search_s(
        base_dn, ldap.SCOPE_SUBTREE, search_filter, attrlist=attrlist
    )


def get_user(conn, base_dn, username: str):
    search_filter = f"(&(objectClass=posixAccount)(uid={username}))"
    return conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter)


list_user_attrs = ["uid", "uidNumber"]


def list_users(conn, base_dn: str, attrlist=list_user_attrs):
    search_filter = "(&(objectClass=posixAccount))"
    return conn.search_s(
        base_dn, ldap.SCOPE_SUBTREE, search_filter, attrlist=attrlist
    )


def create_user(conn, base_dn, days_since_epoch, user: kinds.CreateUserRequest):
    # Validate input parameters
    uid_number = validate_uid_number(user.user_uid)
    shadow_last_change = validate_shadow_last_change(days_since_epoch)
    
    new_user = ldap.modlist.addModlist(
        {
            "objectClass": [
                b"posixAccount",
                b"shadowAccount",
                b"inetOrgPerson",
            ],
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
            "uidNumber": str(uid_number).encode("UTF-8"),
            "shadowLastChange": str(shadow_last_change).encode("UTF-8"),
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


def remove_user_from_group(conn, base_dn, username, group):
    mod_group = [
        (
            ldap.MOD_DELETE,
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
    # Validate input parameter
    shadow_last_change_value = validate_shadow_last_change(days_since_epoch)
    
    mod_shadow = [
        (
            ldap.MOD_DELETE,
            "shadowLastChange",
            None,
        ),
        (
            ldap.MOD_ADD,
            "shadowLastChange",
            [str(shadow_last_change_value).encode("UTF-8")],
        ),
    ]
    return conn.modify_s(
        f"uid={username},ou=People,{base_dn}",
        mod_shadow,
    )
