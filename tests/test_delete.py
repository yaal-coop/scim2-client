import pytest
from httpx import Client
from scim2_models import Error
from scim2_models import Group
from scim2_models import User

from scim2_client import RequestNetworkError
from scim2_client import SCIMClient
from scim2_client import SCIMRequestError


def test_delete_user(httpserver):
    """Nominal case for a User deletion."""
    httpserver.expect_request(
        "/Users/2819c223-7f76-453a-919d-413861904646", method="DELETE"
    ).respond_with_data(status=204, content_type="application/scim+json")

    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim_client = SCIMClient(client, resource_types=(User,))
    response = scim_client.delete(User, "2819c223-7f76-453a-919d-413861904646")
    assert response is None


@pytest.mark.parametrize("code", [400, 401, 403, 404, 412, 500, 501])
def test_errors(httpserver, code):
    """Test error cases defined in RFC7644."""
    httpserver.expect_request(
        "/Users/2819c223-7f76-453a-919d-413861904646", method="DELETE"
    ).respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": str(code),
            "detail": f"{code} error",
        },
        status=code,
    )

    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim_client = SCIMClient(client, resource_types=(User,))
    response = scim_client.delete(User, "2819c223-7f76-453a-919d-413861904646")

    assert response == Error(
        schemas=["urn:ietf:params:scim:api:messages:2.0:Error"],
        status=code,
        detail=f"{code} error",
    )


def test_invalid_resource_type(httpserver):
    """Test that resource_types passed to the method must be part of
    SCIMClient.resource_types."""
    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim_client = SCIMClient(client, resource_types=(User,))
    with pytest.raises(SCIMRequestError, match=r"Unknown resource type"):
        scim_client.delete(Group(display_name="foobar"), id="foobar")


def test_dont_check_response_payload(httpserver):
    """Test the check_response_payload attribute."""
    httpserver.expect_request(
        "/Users/2819c223-7f76-453a-919d-413861904646", method="DELETE"
    ).respond_with_json(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
            "status": "404",
            "detail": "404 error",
        },
        status=404,
    )

    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim_client = SCIMClient(client, resource_types=(User,))
    response = scim_client.delete(
        User, "2819c223-7f76-453a-919d-413861904646", check_response_payload=False
    )
    assert response == {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:Error"],
        "status": "404",
        "detail": "404 error",
    }


def test_request_network_error(httpserver):
    """Test that httpx exceptions are transformed in RequestNetworkError."""
    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim_client = SCIMClient(client, resource_types=(User,))
    with pytest.raises(
        RequestNetworkError, match="Network error happened during request"
    ):
        scim_client.delete(User, "anything", url="http://invalid.test")
