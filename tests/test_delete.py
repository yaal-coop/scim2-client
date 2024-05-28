import pytest
from httpx import Client
from pydantic_scim2 import Error
from pydantic_scim2 import User

from httpx_scim_client import SCIMClient


def test_delete_user(httpserver):
    """Nominal case for a User deletion."""

    httpserver.expect_request(
        "/Users/2819c223-7f76-453a-919d-413861904646", method="DELETE"
    ).respond_with_data(status=204, content_type="application/scim+json")

    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim_client = SCIMClient(client)
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
    scim_client = SCIMClient(client)
    response = scim_client.delete(User, "2819c223-7f76-453a-919d-413861904646")

    assert response == Error(
        schemas=["urn:ietf:params:scim:api:messages:2.0:Error"],
        status=code,
        detail=f"{code} error",
    )
