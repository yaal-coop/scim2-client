from scim2_models import EnterpriseUser
from scim2_models import Group
from scim2_models import ServiceProviderConfig
from scim2_models import User

from scim2_client import SCIMClient


def test_guess_resource_endpoint():
    client = SCIMClient(None, resource_models=[User[EnterpriseUser], Group])
    assert client.resource_endpoint(Group) == "/Groups"
    assert client.resource_endpoint(User) == "/Users"
    assert client.resource_endpoint(User[EnterpriseUser]) == "/Users"

    # This one is special as it does not take an ending 's'
    assert client.resource_endpoint(ServiceProviderConfig) == "/ServiceProviderConfig"
