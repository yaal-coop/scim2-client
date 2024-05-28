import json.decoder
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

from httpx import Client
from httpx import Response
from pydantic import ValidationError
from pydantic_scim2 import Error
from pydantic_scim2 import ListResponse
from pydantic_scim2 import PatchOp
from pydantic_scim2 import Resource
from pydantic_scim2.rfc7644.search_request import SortOrder

from .errors import UnexpectedContentFormat
from .errors import UnexpectedContentType
from .errors import UnexpectedStatusCode

AnyResource = TypeVar("AnyResource", bound=Resource)

BASE_HEADERS = {
    "Accept": "application/scim+json",
    "Content-Type": "application/scim+json",
}


class SCIMClient:
    """An object that perform SCIM requests and validate responses."""

    def __init__(self, client: Client):
        self.client = client

    def check_response(self, response: Response, expected_status_codes: List[int]):
        # TODO: use http-exceptions instead?
        # https://pypi.org/project/http-exceptions
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
            return response.json()
        except json.decoder.JSONDecodeError as exc:
            raise UnexpectedContentFormat(response) from exc

    def create(self, resource: AnyResource) -> Union[AnyResource, Error]: ...

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
        """Perform a GET request to read resources.

        - If `id` is not :data:`None`, the resource with the exact id will be reached.
          Return a `resource_type` object in case of success, or :class:`~pydantic_scim2.Error`.
        - If `id` is :data:`None`, all the resources with the given type will be reached.
          Return a :class:`~pydantic_scim2.ListResponse[resource_type]` object in case of success, or :class:`~pydantic_scim2.Error`.

        :param resource_type: A :class:`~pydantic_scim2.Resource` subtype or :data:`None`
        :param id: The SCIM id of an object to get, or :data:`None`
        """

        if not id:
            expected_type = ListResponse[resource_type]
            url = f"{resource_type.__name__}s"

        else:
            expected_type = resource_type
            url = f"/{resource_type.__name__}s/{id}"

        # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.12
        expected_status_codes = [200, 307, 308, 400, 401, 403, 404, 500, 501]
        response = self.client.get(url)
        response_payload = self.check_response(response, expected_status_codes)

        try:
            return Error.model_validate(response_payload)
        except ValidationError:
            return expected_type.model_validate(response_payload)

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
        """Perform a GET request to read all resources available:

        :param resource_types: Resource type or union of types expected to be read from the response.
        """

        # A query against a server root indicates that all resources within the
        # server SHALL be included, subject to filtering.
        # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.4.2.1

        response = self.client.get("/")

        # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.12
        expected_status_codes = [200, 307, 308, 400, 401, 403, 404, 500, 501]
        response_payload = self.check_response(response, expected_status_codes)

        try:
            return Error.model_validate(response_payload)
        except ValidationError:
            return ListResponse[resource_types].model_validate(response_payload)

    def delete(self, resource_type: Type, id: str) -> Optional[Error]: ...

    def replace(self, resource: AnyResource) -> Union[AnyResource, Error]: ...

    def modify(self, resource: AnyResource, op: PatchOp) -> Optional[AnyResource]: ...
