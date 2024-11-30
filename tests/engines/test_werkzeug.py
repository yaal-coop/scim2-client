import pytest
from scim2_models import ResourceType
from scim2_models import SearchRequest
from scim2_models import User
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response

from scim2_client.engines.werkzeug import TestSCIMClient
from scim2_client.errors import SCIMResponseErrorObject
from scim2_client.errors import UnexpectedContentFormat

scim2_server = pytest.importorskip("scim2_server")
from scim2_server.backend import InMemoryBackend  # noqa: E402
from scim2_server.provider import SCIMProvider  # noqa: E402


@pytest.fixture
def scim_provider():
    provider = SCIMProvider(InMemoryBackend())
    provider.register_schema(User.to_schema())
    provider.register_resource_type(ResourceType.from_resource(User))
    return provider


@pytest.fixture
def scim_client(scim_provider):
    return TestSCIMClient(
        app=scim_provider,
        resource_models=(User,),
        resource_types=[ResourceType.from_resource(User)],
    )


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


def test_no_json():
    """Test that pages that do not return JSON raise an UnexpectedContentFormat error."""

    @Request.application
    def application(request):
        return Response("Hello, World!", content_type="application/scim+json")

    client = TestSCIMClient(app=application, resource_models=(User,))
    with pytest.raises(UnexpectedContentFormat):
        client.query(url="/")
