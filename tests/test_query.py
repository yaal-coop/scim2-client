import datetime

import pytest
from httpx import Client
from scim2_models import Error
from scim2_models import Group
from scim2_models import ListResponse
from scim2_models import Meta
from scim2_models import Resource
from scim2_models import SearchRequest
from scim2_models import ServiceProviderConfig
from scim2_models import User

from scim2_client import SCIMClient
from scim2_client import SCIMRequestError
from scim2_client.client import UnexpectedContentFormat
from scim2_client.client import UnexpectedContentType
from scim2_client.client import UnexpectedStatusCode
from scim2_client.errors import RequestNetworkError
from scim2_client.errors import ResponsePayloadValidationError
from scim2_client.errors import SCIMClientError
from scim2_client.errors import SCIMResponseError
from scim2_client.errors import SCIMResponseErrorObject


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

    httpserver.expect_request("/Users/not-a-scim-object").respond_with_json(
        {"foo": "bar"}, status=200, content_type="application/scim+json"
    )

    httpserver.expect_request("/Users/content-type-with-charset").respond_with_json(
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
        content_type="application/scim+json; charset=utf-8",
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

    httpserver.expect_request("/ServiceProviderConfig").respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
            "documentationUri": "http://example.com/help/scim.html",
            "patch": {"supported": True},
            "bulk": {
                "supported": True,
                "maxOperations": 1000,
                "maxPayloadSize": 1048576,
            },
            "filter": {"supported": True, "maxResults": 200},
            "changePassword": {"supported": True},
            "sort": {"supported": True},
            "etag": {"supported": True},
            "authenticationSchemes": [
                {
                    "name": "OAuth Bearer Token",
                    "description": "Authentication scheme using the OAuth Bearer Token Standard",
                    "specUri": "http://www.rfc-editor.org/info/rfc6750",
                    "documentationUri": "http://example.com/help/oauth.html",
                    "type": "oauthbearertoken",
                    "primary": True,
                },
                {
                    "name": "HTTP Basic",
                    "description": "Authentication scheme using the HTTP Basic Standard",
                    "specUri": "http://www.rfc-editor.org/info/rfc2617",
                    "documentationUri": "http://example.com/help/httpBasic.html",
                    "type": "httpbasic",
                },
            ],
            "meta": {
                "location": "https://example.com/v2/ServiceProviderConfig",
                "resourceType": "ServiceProviderConfig",
                "created": "2010-01-23T04:56:22Z",
                "lastModified": "2011-05-13T04:42:34Z",
                "version": 'W\\/"3694e05e9dff594"',
            },
        }
    )
    return httpserver


@pytest.fixture
def client(httpserver):
    return Client(base_url=f"http://localhost:{httpserver.port}")


def test_user_with_valid_id(client):
    """Test that querying an existing user with an id correctly instantiate an User object."""
    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    response = scim_client.query(
        User, "2819c223-7f76-453a-919d-413861904646", raise_scim_errors=False
    )
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
    """Test that querying an user with an invalid id instantiate an Error object."""
    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    response = scim_client.query(User, "unknown", raise_scim_errors=False)
    assert response == Error(detail="Resource unknown not found", status=404)


def test_raise_scim_errors(client):
    """Test that querying an user with an invalid id instantiate an Error object."""
    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    with pytest.raises(
        SCIMResponseErrorObject,
        match="The server returned a SCIM Error object: Resource unknown not found",
    ):
        scim_client.query(User, "unknown", raise_scim_errors=True)


def test_all_users(client):
    """Test that querying all existing users instantiate a ListResponse object."""
    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
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


def test_custom_url(client):
    """Test that querying by passing the 'url' parameter directly to httpx is accepted."""
    scim_client = SCIMClient(client, resource_models=(User, Group))
    response = scim_client.query(url="/Users/2819c223-7f76-453a-919d-413861904646")
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


def test_no_result(client):
    """Test querying a resource with no object."""
    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    response = scim_client.query(Group)
    assert response == ListResponse[Group](total_results=0, resources=None)


def test_bad_request(client):
    """Test querying a resource unknown from the server instantiate an Error object."""
    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    response = scim_client.query(User, "bad-request", raise_scim_errors=False)
    assert response == Error(status=400, detail="Bad request")


def test_resource_unknown_by_server(client):
    """Test querying a resource unknown from the server instantiate an Error object."""

    class Foobar(Resource):
        pass

    scim_client = SCIMClient(client, resource_models=(Foobar,))
    response = scim_client.query(Foobar, raise_scim_errors=False)
    assert response == Error(status=404, detail="Invalid Resource")


def test_bad_resource_model(client):
    """Test querying a resource unknown from the client raise a SCIMResponseError."""
    scim_client = SCIMClient(client, resource_models=(User,))
    with pytest.raises(
        SCIMResponseError,
        match="Expected type User but got unknown resource with schemas: urn:ietf:params:scim:schemas:core:2.0:Group",
    ):
        scim_client.query(User, "its-a-group")


def test_all(client):
    """Test querying all resources from the server instation a ListResponse object."""
    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    response = scim_client.query()
    assert isinstance(response, ListResponse)
    assert response.total_results == 2
    user, group = response.resources
    assert isinstance(user, User)
    assert isinstance(group, Group)


def test_all_unexpected_type(client):
    """Test retrieving a payload for an object which type has not been passed in parameters raise a ResponsePayloadValidationError."""
    scim_client = SCIMClient(client, resource_models=(User,))
    with pytest.raises(
        ResponsePayloadValidationError, match="Server response payload validation error"
    ):
        scim_client.query()


def test_response_is_not_json(client):
    """Test situations where servers return an invalid JSON object."""
    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    with pytest.raises(UnexpectedContentFormat):
        scim_client.query(User, "not-json")


def test_not_a_scim_object(client):
    """Test retrieving a valid JSON object without a schema."""
    scim_client = SCIMClient(client, resource_models=(User,))
    with pytest.raises(
        SCIMResponseError,
        match="Expected type User but got undefined object with no schema",
    ):
        scim_client.query(User, "not-a-scim-object")


def test_dont_check_response_payload(httpserver, client):
    """Test the check_response_payload attribute."""
    scim_client = SCIMClient(client, resource_models=(User,))
    response = scim_client.query(
        User, "not-a-scim-object", check_response_payload=False
    )
    assert response == {"foo": "bar"}


def test_response_bad_status_code(client):
    """Test situations where servers return an invalid status code."""
    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    with pytest.raises(UnexpectedStatusCode):
        scim_client.query(User, "status-201")
    scim_client.query(User, "status-201", expected_status_codes=None)


def test_response_content_type_with_charset(client):
    """Test situations where servers return a valid content-type with a charset information."""
    scim_client = SCIMClient(client, resource_models=(User, Group))
    user = scim_client.query(User, "content-type-with-charset")
    assert isinstance(user, User)


def test_response_bad_content_type(client):
    """Test situations where servers return an invalid content-type response."""
    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    with pytest.raises(UnexpectedContentType):
        scim_client.query(User, "bad-content-type")


def test_search_request(httpserver, client):
    query_string = "attributes=userName&attributes=displayName&filter=userName%20Eq%20%22john%22&sortBy=userName&sortOrder=ascending&startIndex=1&count=10"

    httpserver.expect_request(
        "/Users/with-qs", query_string=query_string
    ).respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "with-qs",
            "userName": "bjensen@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2010-01-23T04:56:22Z",
                "lastModified": "2011-05-13T04:42:34Z",
                "version": 'W\\/"3694e05e9dff590"',
                "location": "https://example.com/v2/Users/with-qs",
            },
        },
        status=200,
    )
    req = SearchRequest(
        attributes=["userName", "displayName"],
        filter='userName Eq "john"',
        sort_by="userName",
        sort_order=SearchRequest.SortOrder.ascending,
        start_index=1,
        count=10,
    )

    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    response = scim_client.query(User, "with-qs", req)
    assert isinstance(response, User)
    assert response.id == "with-qs"


def test_query_dont_check_request_payload(httpserver, client):
    """Test the check_request_payload attribute on query."""
    query_string = "attributes=userName&attributes=displayName&excluded_attributes=timezone&excluded_attributes=phoneNumbers&filter=userName%20Eq%20%22john%22&sort_by=userName&sort_order=ascending&start_index=1&count=10"

    httpserver.expect_request(
        "/Users/with-qs", query_string=query_string
    ).respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": "with-qs",
            "userName": "bjensen@example.com",
            "meta": {
                "resourceType": "User",
                "created": "2010-01-23T04:56:22Z",
                "lastModified": "2011-05-13T04:42:34Z",
                "version": 'W\\/"3694e05e9dff590"',
                "location": "https://example.com/v2/Users/with-qs",
            },
        },
        status=200,
    )
    req = {
        "attributes": ["userName", "displayName"],
        "excluded_attributes": ["timezone", "phoneNumbers"],
        "filter": 'userName Eq "john"',
        "sort_by": "userName",
        "sort_order": SearchRequest.SortOrder.ascending.value,
        "start_index": 1,
        "count": 10,
    }

    scim_client = SCIMClient(
        client,
        resource_models=(
            User,
            Group,
        ),
    )
    response = scim_client.query(User, "with-qs", req, check_request_payload=False)
    assert isinstance(response, User)
    assert response.id == "with-qs"


def test_invalid_resource_model(httpserver):
    """Test that resource_models passed to the method must be part of SCIMClient.resource_models."""
    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim_client = SCIMClient(client, resource_models=(User,))
    with pytest.raises(SCIMRequestError, match=r"Unknown resource type"):
        scim_client.query(Group)


def test_service_provider_config_endpoint(client):
    """Test that querying the /ServiceProviderConfig enpdoint correctly returns a ServiceProviderConfig (and not a ListResponse)."""
    scim_client = SCIMClient(client, resource_models=(ServiceProviderConfig,))
    response = scim_client.query(ServiceProviderConfig)
    assert isinstance(response, ServiceProviderConfig)


def test_service_provider_config_endpoint_with_an_id(client):
    """Test that querying the /ServiceProviderConfig with an id raise an exception."""
    scim_client = SCIMClient(client, resource_models=(ServiceProviderConfig,))

    with pytest.raises(
        SCIMClientError, match="ServiceProviderConfig cannot have an id"
    ):
        scim_client.query(ServiceProviderConfig, "dummy")


def test_request_network_error(client):
    """Test that httpx exceptions are transformed in RequestNetworkError."""
    scim_client = SCIMClient(client, resource_models=(User,))
    with pytest.raises(
        RequestNetworkError, match="Network error happened during request"
    ):
        scim_client.query(url="http://invalid.test")
