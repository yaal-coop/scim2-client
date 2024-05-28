import datetime
from typing import Union

import pytest
from httpx import Client
from pydantic import ValidationError
from pydantic_scim2 import Error
from pydantic_scim2 import Group
from pydantic_scim2 import ListResponse
from pydantic_scim2 import Meta
from pydantic_scim2 import Resource
from pydantic_scim2 import User

from httpx_scim_client import SCIMClient
from httpx_scim_client.client import UnexpectedContentFormat
from httpx_scim_client.client import UnexpectedContentType
from httpx_scim_client.client import UnexpectedStatusCode


@pytest.fixture
def httpserver(httpserver):
    httpserver.expect_request(
        "/Users/2819c223-7f76-453a-919d-413861904646"
    ).respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "2819c223-7f76-453a-919d-413861904646",
            "userName": "bjensen@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2010-01-23T04:56:22Z",
                "lastModified": "2011-05-13T04:42:34Z",
                "version": 'W\\/"3694e05e9dff590"',
                "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
            },
        },
        status=200,
    )

    httpserver.expect_request("/Users/unknown").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "detail": "Resource unknown not found",
            "status": "404",
        },
        status=404,
    )

    httpserver.expect_request("/Users/bad-request").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "detail": "Bad request",
            "status": "400",
        },
        status=400,
    )

    httpserver.expect_request("/Users/status-201").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "2819c223-7f76-453a-919d-413861904646",
            "userName": "bjensen@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2010-01-23T04:56:22Z",
                "lastModified": "2011-05-13T04:42:34Z",
                "version": 'W\\/"3694e05e9dff590"',
                "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
            },
        },
        status=201,
    )

    httpserver.expect_request("/Users/not-json").respond_with_data(
        "foobar", status=200, content_type="application/scim+json"
    )

    httpserver.expect_request("/Users/bad-content-type").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "2819c223-7f76-453a-919d-413861904646",
            "userName": "bjensen@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2010-01-23T04:56:22Z",
                "lastModified": "2011-05-13T04:42:34Z",
                "version": 'W\\/"3694e05e9dff590"',
                "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
            },
        },
        status=200,
        content_type="application/text",
    )

    httpserver.expect_request("/Users/its-a-group").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": "e9e30dba-f08f-4109-8486-d5c6a331660a",
            "displayName": "Tour Guides",
            "members": [
                {
                    "value": "2819c223-7f76-453a-919d-413861904646",
                    "$ref": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
                    "display": "Babs Jensen",
                },
            ],
            "meta": {
                "resourceType": "Group",
                "created": "2010-01-23T04:56:22Z",
                "lastModified": "2011-05-13T04:42:34Z",
                "version": 'W\\/"3694e05e9dff592"',
                "location": "https://example.com/v2/Groups/e9e30dba-f08f-4109-8486-d5c6a331660a",
            },
        },
        status=200,
    )

    httpserver.expect_request("/Users").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 2,
            "Resources": [
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                    "id": "2819c223-7f76-453a-919d-413861904646",
                    "userName": "bjensen@example.com",
                    "meta": {
                        "resourceType": "User",
                        "created": "2010-01-23T04:56:22Z",
                        "lastModified": "2011-05-13T04:42:34Z",
                        "version": 'W\\/"3694e05e9dff590"',
                        "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
                    },
                },
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                    "id": "074860c7-70e9-4db5-ad40-a32bab8be11d",
                    "userName": "jsmith@example.com",
                    "meta": {
                        "resourceType": "User",
                        "created": "2010-02-23T04:56:22Z",
                        "lastModified": "2011-06-13T04:42:34Z",
                        "version": 'W\\/"deadbeef0000"',
                        "location": "https://example.com/v2/Users/074860c7-70e9-4db5-ad40-a32bab8be11d",
                    },
                },
            ],
        },
        status=200,
    )

    httpserver.expect_request("/Groups").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 0,
        },
        status=200,
    )

    httpserver.expect_request("/Foobars").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "detail": "Invalid Resource",
            "status": "404",
        },
        status=404,
    )

    httpserver.expect_request("/").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 2,
            "Resources": [
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                    "id": "2819c223-7f76-453a-919d-413861904646",
                    "userName": "bjensen@example.com",
                    "meta": {
                        "resourceType": "User",
                        "created": "2010-01-23T04:56:22Z",
                        "lastModified": "2011-05-13T04:42:34Z",
                        "version": 'W\\/"3694e05e9dff590"',
                        "location": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
                    },
                },
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "id": "e9e30dba-f08f-4109-8486-d5c6a331660a",
                    "displayName": "Tour Guides",
                    "members": [
                        {
                            "value": "2819c223-7f76-453a-919d-413861904646",
                            "$ref": "https://example.com/v2/Users/2819c223-7f76-453a-919d-413861904646",
                            "display": "Babs Jensen",
                        },
                    ],
                    "meta": {
                        "resourceType": "Group",
                        "created": "2010-01-23T04:56:22Z",
                        "lastModified": "2011-05-13T04:42:34Z",
                        "version": 'W\\/"3694e05e9dff592"',
                        "location": "https://example.com/v2/Groups/e9e30dba-f08f-4109-8486-d5c6a331660a",
                    },
                },
            ],
        },
        status=200,
    )

    return httpserver


@pytest.fixture
def client(httpserver):
    return Client(base_url=f"http://localhost:{httpserver.port}")


def test_user_with_valid_id(client):
    """Test that querying an existing user with an id correctly instantiate an
    User object."""

    scim_client = SCIMClient(client)
    response = scim_client.query(User, "2819c223-7f76-453a-919d-413861904646")
    assert response == User(
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


def test_user_with_invalid_id(client):
    """Test that querying an user with an invalid id instantiate an Error
    object."""

    scim_client = SCIMClient(client)
    response = scim_client.query(User, "unknown")
    assert response == Error(detail="Resource unknown not found", status=404)


def test_all_users(client):
    """Test that querying all existing users instantiate a ListResponse
    object."""

    scim_client = SCIMClient(client)
    response = scim_client.query(User)
    assert response == ListResponse[User](
        total_results=2,
        resources=[
            User(
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
            ),
            User(
                id="074860c7-70e9-4db5-ad40-a32bab8be11d",
                user_name="jsmith@example.com",
                meta=Meta(
                    resource_type="User",
                    created=datetime.datetime(
                        2010, 2, 23, 4, 56, 22, tzinfo=datetime.timezone.utc
                    ),
                    last_modified=datetime.datetime(
                        2011, 6, 13, 4, 42, 34, tzinfo=datetime.timezone.utc
                    ),
                    version='W\\/"deadbeef0000"',
                    location="https://example.com/v2/Users/074860c7-70e9-4db5-ad40-a32bab8be11d",
                ),
            ),
        ],
    )


def test_no_group(client):
    """Test querying a resource with no object."""

    scim_client = SCIMClient(client)
    response = scim_client.query(Group)
    assert response == ListResponse[Group](total_results=0, resources=None)


def test_bad_request(client):
    """Test querying a resource unkown from the server instantiate an Error
    object."""

    scim_client = SCIMClient(client)
    response = scim_client.query(User, "bad-request")
    assert response == Error(status=400, detail="Bad request")


def test_resource_unknown_by_server(client):
    """Test querying a resource unkown from the server instantiate an Error
    object."""

    class Foobar(Resource):
        pass

    scim_client = SCIMClient(client)
    response = scim_client.query(Foobar)
    assert response == Error(status=404, detail="Invalid Resource")


def test_bad_resource_type(client):
    """Test querying a resource unkown from the client raise a
    ValidationError."""

    scim_client = SCIMClient(client)
    with pytest.raises(ValidationError):
        scim_client.query(User, "its-a-group")


def test_all(client):
    """Test querying all resources from the server instation a ListResponse
    object."""

    scim_client = SCIMClient(client)
    response = scim_client.query_all(Union[User, Group])
    assert isinstance(response, ListResponse)
    assert response.total_results == 2
    user, group = response.resources
    assert isinstance(user, User)
    assert isinstance(group, Group)


def test_all_unexpected_type(client):
    """Test retrieving a payload for an object which type has not been passed
    in parameters raise a ValidationError."""

    scim_client = SCIMClient(client)
    with pytest.raises(ValidationError):
        scim_client.query_all(User)


def test_response_is_not_json(client):
    """Test sitations where servers return an invalid JSON object."""

    scim_client = SCIMClient(client)
    with pytest.raises(UnexpectedContentFormat):
        scim_client.query(User, "not-json")


def test_response_bad_status_code(client):
    """Test sitations where servers return an invalid status code."""

    scim_client = SCIMClient(client)
    with pytest.raises(UnexpectedStatusCode):
        scim_client.query(User, "status-201")


def test_response_bad_content_type(client):
    """Test sitations where servers return an invalid content-type response."""

    scim_client = SCIMClient(client)
    with pytest.raises(UnexpectedContentType):
        scim_client.query(User, "bad-content-type")
