# portal-ldap

A small service to allow the CyVerse user portal to interact with LDAP.

## Building

Check out the Dockerfile for hints as to how to get this thing to build.

To build the container image:
```bash
> docker build --rm -t <image repo> .
```

## Configuration

To configure the service, set the following environment variables:

* `LDAP_URL` - An LDAP connection url: Example: `ldap://my-ldap-server.example.org`.
* `LDAP_USER` - The user for the LDAP connection. Example: `cn=Person,dc=example,dc=org`.
* `LDAP_PASSWORD` - The user's password for the LDAP connection.
* `LDAP_BASE_DN` - The base DN to add to LDAP queries. Example: `dc=example,dc=org`.
