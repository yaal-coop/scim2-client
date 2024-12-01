import threading
import wsgiref.simple_server

import portpicker
import pytest
from httpx import AsyncClient
from httpx import Client
from scim2_models import SearchRequest
from scim2_models import ServiceProviderConfig

from scim2_client.engines.httpx import AsyncSCIMClient
from scim2_client.engines.httpx import SyncSCIMClient
from scim2_client.errors import SCIMResponseErrorObject

scim2_server = pytest.importorskip("scim2_server")
from scim2_server.backend import InMemoryBackend  # noqa: E402
from scim2_server.provider import SCIMProvider  # noqa: E402
from scim2_server.utils import load_default_resource_types  # noqa: E402
from scim2_server.utils import load_default_schemas  # noqa: E402


@pytest.fixture(scope="session")
def server():
    backend = InMemoryBackend()
    provider = SCIMProvider(backend)
    for schema in load_default_schemas().values():
        provider.register_schema(schema)
    for resource_type in load_default_resource_types().values():
        provider.register_resource_type(resource_type)
    host = "localhost"
    port = portpicker.pick_unused_port()
    httpd = wsgiref.simple_server.make_server(host, port, provider)

    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.start()
    try:
        yield host, port
    finally:
        httpd.shutdown()
        server_thread.join()


def test_sync_engine(server):
    host, port = server
    client = Client(base_url=f"http://{host}:{port}")
    scim_client = SyncSCIMClient(client)

    scim_client.discover()
    assert isinstance(scim_client.service_provider_config, ServiceProviderConfig)
    User = scim_client.get_resource_model("User")

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


async def test_async_engine(server):
    host, port = server
    client = AsyncClient(base_url=f"http://{host}:{port}")
    scim_client = AsyncSCIMClient(client)

    await scim_client.discover()
    assert isinstance(scim_client.service_provider_config, ServiceProviderConfig)
    User = scim_client.get_resource_model("User")

    request_user = User(user_name="foo", display_name="bar")
    response_user = await scim_client.create(request_user)
    assert response_user.user_name == "foo"
    assert response_user.display_name == "bar"

    response_user = await scim_client.query(User, response_user.id)
    assert response_user.user_name == "foo"
    assert response_user.display_name == "bar"

    req = SearchRequest()
    response_users = await scim_client.search(req)
    assert response_users.resources[0].user_name == "foo"
    assert response_users.resources[0].display_name == "bar"

    request_user = User(id=response_user.id, user_name="foo", display_name="baz")
    response_user = await scim_client.replace(request_user)
    assert response_user.user_name == "foo"
    assert response_user.display_name == "baz"

    response_user = await scim_client.query(User, response_user.id)
    assert response_user.user_name == "foo"
    assert response_user.display_name == "baz"

    await scim_client.delete(User, response_user.id)
    with pytest.raises(SCIMResponseErrorObject):
        await scim_client.query(User, response_user.id)
