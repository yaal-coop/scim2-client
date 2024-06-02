# scim2-client

A SCIM client Python library built upon [scim2-models](https://scim2-models.readthedocs.io) and [httpx](https://github.com/encode/httpx),
that pythonically build requests and parse responses,
following the [RFC7643](https://datatracker.ietf.org/doc/html/rfc7643.html) and [RFC7644](https://datatracker.ietf.org/doc/html/rfc7644.html) specifications.

It aims to be used in SCIM client applications, or in unit tests for SCIM server applications.

## Installation

```shell
pip install scim2-client
```

## Usage

Check the [tutorial](https://scim2-client.readthedocs.io/en/latest/tutorial.html) and the [reference](https://scim2-client.readthedocs.io/en/latest/reference.html) for more details.

Here is an example of usage:

```python
import datetime
from httpx import Client
from scim2_models import User, EnterpriseUserUser, Group, Error
from scim2_client import SCIMClient

client = Client(base_url=f"https://auth.example/scim/v2", headers={"Authorization": "Bearer foobar"})
scim = SCIMClient(client, resource_types=(User[EnterpriseUser], Group))

# Query resources
user = scim.query(User, "2819c223-7f76-453a-919d-413861904646")
assert user.user_name == "bjensen@example.com"
assert user.meta.last_updated == datetime.datetime(
    2024, 4, 13, 12, 0, 0, tzinfo=datetime.timezone.utc
)

# Update resources
user.display_name = "Babes Jensen"
user = scim.replace(user)
assert user.display_name == "Babes Jensen"
assert user.meta.last_updated == datetime.datetime(
    2024, 4, 13, 12, 0, 30, tzinfo=datetime.timezone.utc
)

# Create resources
payload = User(user_name="bjensen@example.com")
response = scim.create(user)
assert isinstance(response, Error)
assert response.detail == "One or more of the attribute values are already in use or are reserved."
```
