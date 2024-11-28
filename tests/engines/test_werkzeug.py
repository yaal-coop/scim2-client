import pytest
from scim2_models import ResourceType
from scim2_models import SearchRequest
from scim2_models import User

from scim2_client.engines.werkzeug import TestSCIMClient
from scim2_client.errors import SCIMResponseErrorObject

scim2_server = pytest.importorskip("scim2_server")
from scim2_server.backend import InMemoryBackend  # noqa: E402
from scim2_server.provider import SCIMProvider  # noqa: E402

# Avoid pytest believing this is a test class
TestSCIMClient.__test__ = False  # type: ignore


@pytest.fixture
def scim_provider():
    provider = SCIMProvider(InMemoryBackend())
    provider.register_schema(User.to_schema())
    provider.register_resource_type(
        ResourceType(
            id="User",
            name="User",
            endpoint="/Users",
            schema="urn:ietf:params:scim:schemas:core:2.0:User",
        )
    )
    return provider


@pytest.fixture
def scim_client(scim_provider):
    return TestSCIMClient(app=scim_provider, resource_models=(User,))


def test_werkzeug_engine(scim_client):
    request_user = User(user_name="foo", display_name="bar")
    response_user = scim_client.create(request_user)
    assert response_user.user_name == "foo"
    assert response_user.display_name == "bar"

    response_user = scim_client.query(User, response_user.id)
    assert response_user.user_name == "foo"
    assert response_user.display_name == "bar"

    req = SearchRequest()
    response_users = scim_client.search(req)
    assert response_users.resources[0].user_name == "foo"
    assert response_users.resources[0].display_name == "bar"

    request_user = User(id=response_user.id, user_name="foo", display_name="baz")
    response_user = scim_client.replace(request_user)
    assert response_user.user_name == "foo"
    assert response_user.display_name == "baz"

    response_user = scim_client.query(User, response_user.id)
    assert response_user.user_name == "foo"
    assert response_user.display_name == "baz"

    scim_client.delete(User, response_user.id)
    with pytest.raises(SCIMResponseErrorObject):
        scim_client.query(User, response_user.id)
