import json.decoder
from typing import List
from typing import Optional
from typing import Type
from typing import Union

from httpx import Client
from httpx import Response
from pydantic import ValidationError
from pydantic_scim2 import AnyResource
from pydantic_scim2 import Error
from pydantic_scim2 import ListResponse
from pydantic_scim2 import PatchOp
from pydantic_scim2 import SortOrder

from .errors import UnexpectedContentFormat
from .errors import UnexpectedContentType
from .errors import UnexpectedStatusCode

BASE_HEADERS = {
    "Accept": "application/scim+json",
    "Content-Type": "application/scim+json",
}


class SCIMClient:
    """An object that perform SCIM requests and validate responses."""

    def __init__(self, client: Client):
        self.client = client

    def resource_endpoint(self, resource_type: Type):
        return f"/{resource_type.__name__}s"

    def check_response(
        self, response: Response, expected_status_codes: List[int], expected_type: Type
    ):
        if response.status_code not in expected_status_codes:
            raise UnexpectedStatusCode(response)

        # Interoperability considerations:  The "application/scim+json" media
        # type is intended to identify JSON structure data that conforms to
        # the SCIM protocol and schema specifications.  Older versions of
        # SCIM are known to informally use "application/json".
        # https://datatracker.ietf.org/doc/html/rfc7644.html#section-8.1

        expected_response_content_types = ("application/scim+json", "application/json")
        if response.headers.get("content-type") not in expected_response_content_types:
            raise UnexpectedContentType(response)

        # In addition to returning an HTTP response code, implementers MUST return
        # the errors in the body of the response in a JSON format
        # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.12

        try:
            response_payload = response.json()
        except json.decoder.JSONDecodeError as exc:
            raise UnexpectedContentFormat(response) from exc

        try:
            return Error.model_validate(response_payload)
        except ValidationError:
            return expected_type.model_validate(response_payload)

    def create(self, resource: AnyResource) -> Union[AnyResource, Error]:
        """Perform a POST request to create, as defined in :rfc:`RFC7644 §3.3
        <7644#section-3.3>`."""

        url = self.resource_endpoint(resource.__class__)
        dump = resource.model_dump(exclude_none=True, by_alias=True, mode="json")
        response = self.client.post(url, json=dump)

        expected_status_codes = [
            # Resource creation HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644#section-3.3
            201,
            409,
            # Default HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.12
            307,
            308,
            400,
            401,
            403,
            404,
            500,
        ]
        return self.check_response(response, expected_status_codes, resource.__class__)

    def query(
        self,
        resource_type: Type,
        id: Optional[str] = None,
        attributes: Optional[List[str]] = None,
        excluded_attributes: Optional[List[str]] = None,
        filter: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[SortOrder] = None,
        start_index: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Union[AnyResource, ListResponse[AnyResource], Error]:
        """Perform a GET request to read resources, as defined in :rfc:`RFC7644
        §3.4.2 <7644#section-3.4.2>`.

        - If `id` is not :data:`None`, the resource with the exact id will be reached.
          Return a `resource_type` object in case of success, or :class:`~pydantic_scim2.Error`.
        - If `id` is :data:`None`, all the resources with the given type will be reached.
          Return a :class:`~pydantic_scim2.ListResponse[resource_type]` object in case of success, or :class:`~pydantic_scim2.Error`.

        :param resource_type: A :class:`~pydantic_scim2.Resource` subtype or :data:`None`
        :param id: The SCIM id of an object to get, or :data:`None`
        """

        if not id:
            expected_type = ListResponse[resource_type]
            url = self.resource_endpoint(resource_type)

        else:
            expected_type = resource_type
            url = self.resource_endpoint(resource_type) + f"/{id}"

        expected_status_codes = [
            # Resource querying HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644#section-3.4.2
            200,
            400,
            # Default HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.12
            307,
            308,
            401,
            403,
            404,
            500,
        ]
        response = self.client.get(url)
        return self.check_response(response, expected_status_codes, expected_type)

    def query_all(
        self,
        resource_types: Type,
        attributes: Optional[List[str]] = None,
        excluded_attributes: Optional[List[str]] = None,
        filter: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[SortOrder] = None,
        start_index: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Union[AnyResource, ListResponse[AnyResource], Error]:
        """Perform a GET request to read all available resources, as defined in
        :rfc:`RFC7644 §3.4.2.1 <7644#section-3.4.2.1>`.

        :param resource_types: Resource type or union of types expected
            to be read from the response.
        """

        # A query against a server root indicates that all resources within the
        # server SHALL be included, subject to filtering.
        # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.4.2.1

        response = self.client.get("/")

        expected_status_codes = [
            # Resource querying HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644#section-3.4.2
            200,
            400,
            # Default HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.12
            307,
            308,
            401,
            403,
            404,
            500,
            501,
        ]
        return self.check_response(
            response, expected_status_codes, ListResponse[resource_types]
        )

    def delete(self, resource_type: Type, id: str) -> Optional[Error]: ...

    def replace(self, resource: AnyResource) -> Union[AnyResource, Error]: ...

    def modify(self, resource: AnyResource, op: PatchOp) -> Optional[AnyResource]: ...
