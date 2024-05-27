from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

from httpx import Client
from pydantic import ValidationError
from pydantic_scim2 import Error
from pydantic_scim2 import ListResponse
from pydantic_scim2 import PatchOp
from pydantic_scim2 import Resource
from pydantic_scim2.rfc7644.search_request import SortOrder

# TODO: Force AllResource to be a union of subclasses of Resource
AllResources = TypeVar("AllResources")

# TODO: Force AnyResource to be part of AllResources
AnyResource = TypeVar("AnyResource", bound=Resource)

BASE_HEADERS = {
    "Accept": "application/scim+json",
    "Content-Type": "application/scim+json",
}


class RawSCIMClient:
    def __init__(
        self,
        client: Client,
    ):
        self.client = client

    def create(self, resource: AnyResource) -> Union[AnyResource, Error]: ...

    def query(
        self,
        resource_type: Optional[Type] = None,
        id: Optional[str] = None,
        attributes: Optional[List[str]] = None,
        excluded_attributes: Optional[List[str]] = None,
        filter: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[SortOrder] = None,
        start_index: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Perform a GET request to read resources.

        - If `resource_type` and `id` are not :data:`None`, the resource with the exact id will be reached.
        - If `resource_type` is not :data:`None` and `id` is :data:`None`, all the resources with the given type will be reached.
        - If `resource_type` and `id` are :data:`None`, all the resources matching the query will be returned.

        :param resource_type: A :pydantic_model:`~pydantic_scim2.Resource` subtype or :data:`None`
        :param id: The SCIM id of an object to get, or :data:`None`
        """

        if not resource_type:
            url = "/"

        elif not id:
            url = f"{resource_type.__name__}s"

        else:
            url = f"/{resource_type.__name__}s/{id}"

        response = self.client.get(url)
        print(url)
        print(response)
        return response.json()

    def delete(self, resource_type: Type, id: str) -> Optional[Error]: ...

    def replace(self, resource: AnyResource) -> Union[AnyResource, Error]: ...

    def modify(self, resource: AnyResource, op: PatchOp) -> Optional[AnyResource]: ...


class SCIMClient(RawSCIMClient, Generic[AllResources]):
    def create(self, resource: AnyResource) -> Union[AnyResource, Error]: ...

    def query(
        self,
        resource_type: Optional[Type] = None,
        id: Optional[str] = None,
        attributes: Optional[List[str]] = None,
        excluded_attributes: Optional[List[str]] = None,
        filter: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[SortOrder] = None,
        start_index: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Union[
        AnyResource, ListResponse[AnyResource], ListResponse[AllResources], Error
    ]:
        """Perform a GET request to read resources.

        - If `resource_type` and `id` are not :data:`None`, the resource with the exact id will be reached.
          Return a `resource_type` object in case of success, or :class:`~pydantic_scim2.Error`.
        - If `resource_type` is not :data:`None` and `id` is :data:`None`, all the resources with the given type will be reached.
          Return a :class:`~pydantic_scim2.ListResponse[resource_type]` object in case of success, or :class:`~pydantic_scim2.Error`.
        - If `resource_type` and `id` are :data:`None`, all the resources matching the query will be returned.
          Return a :class:`~pydantic_scim2.ListResponse[AnyResource]` object in case of success, or :class:`~pydantic_scim2.Error`.

        :param resource_type: A :class:`~pydantic_scim2.Resource` subtype or :data:`None`
        :param id: The SCIM id of an object to get, or :data:`None`
        """

        if not resource_type:
            expected_type = ListResponse[AllResources]

        elif not id:
            expected_type = ListResponse[resource_type]

        else:
            expected_type = resource_type

        response_payload = super().query(
            resource_type=resource_type,
            id=id,
            attributes=attributes,
            excluded_attributes=excluded_attributes,
            filter=filter,
            sort_by=sort_by,
            sort_order=sort_order,
            start_index=start_index,
            count=count,
        )

        try:
            return Error.model_validate(response_payload)
        except ValidationError:
            return expected_type.model_validate(response_payload)

    def delete(self, resource_type: Type, id: str) -> Optional[Error]: ...

    def replace(self, resource: AnyResource) -> Union[AnyResource, Error]: ...

    def modify(self, resource: AnyResource, op: PatchOp) -> Optional[AnyResource]: ...
