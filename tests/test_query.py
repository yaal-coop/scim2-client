import datetime
from typing import Union

from httpx import Client
from pydantic_scim2 import Group
from pydantic_scim2 import Meta
from pydantic_scim2 import User

from httpx_scim_client import SCIMClient


def test_query_user_with_id(httpserver):
    id = "2819c223-7f76-453a-919d-413861904646"
    response_payload = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "id": id,
        "userName": "bjensen@example.com",
        "meta": {
            "resourceType": "User",
            "created": "2010-01-23T04:56:22Z",
            "lastModified": "2011-05-13T04:42:34Z",
            "version": 'W\\/"3694e05e9dff590"',
            "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
        },
    }
    httpserver.expect_request(f"/Users/{id}").respond_with_json(response_payload)

    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim_client = SCIMClient[Union[User, Group]](client)
    user = scim_client.query(User, id)
    assert user == User(
        id="2819c223-7f76-453a-919d-413861904646",
        user_name="bjensen@example.com",
        meta=Meta(
            resource_type="User",
            created=datetime.datetime(
                2010, 1, 23, 4, 56, 22, tzinfo=datetime.timezone.utc
            ),
            last_modified=datetime.datetime(
                2011, 5, 13, 4, 42, 34, tzinfo=datetime.timezone.utc
            ),
            version='W\\/"3694e05e9dff590"',
            location="https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
        ),
    )
