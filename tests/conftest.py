import pytest
from httpx import Client
from scim2_models import Group
from scim2_models import ResourceType
from scim2_models import User

from scim2_client.engines.httpx import SyncSCIMClient


@pytest.fixture
def sync_client(httpserver):
    client = Client(base_url=f"http://localhost:{httpserver.port}")
    scim_client = SyncSCIMClient(
        client,
        resource_models=[User, Group],
        resource_types=[
            ResourceType.from_resource(User),
            ResourceType.from_resource(Group),
        ],
    )
    return scim_client
