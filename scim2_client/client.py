import json
import json.decoder
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import Union

from httpx import Client
from httpx import Response
from pydantic import ValidationError
from scim2_models import AnyResource
from scim2_models import Context
from scim2_models import Error
from scim2_models import ListResponse
from scim2_models import PatchOp
from scim2_models import SearchRequest

from .errors import UnexpectedContentFormat
from .errors import UnexpectedContentType
from .errors import UnexpectedStatusCode

BASE_HEADERS = {
    "Accept": "application/scim+json",
    "Content-Type": "application/scim+json",
}


class SCIMClient:
    """An object that perform SCIM requests and validate responses."""

    def __init__(self, client: Client, resource_types: Optional[Tuple[Type]] = None):
        self.client = client
        self.resource_types = resource_types or ()

    def check_resource_type(self, resource_type):
        if resource_type not in self.resource_types:
            raise ValueError(f"Unknown resource type: '{resource_type}'")

    def resource_endpoint(self, resource_type: Type):
        return f"/{resource_type.__name__}s"

    def check_response(
        self,
        response: Response,
        expected_status_codes: List[int],
        expected_type: Optional[Type] = None,
        scim_ctx: Optional[Context] = None,
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

        if response.status_code in (204, 205):
            response_payload = None

        else:
            try:
                response_payload = response.json()
            except json.decoder.JSONDecodeError as exc:
                raise UnexpectedContentFormat(response) from exc

        try:
            return Error.model_validate(response_payload)
        except ValidationError:
            pass

        if expected_type:
            return expected_type.model_validate(response_payload, scim_ctx=scim_ctx)

        return response_payload

    def create(self, resource: AnyResource, **kwargs) -> Union[AnyResource, Error]:
        """Perform a POST request to create, as defined in :rfc:`RFC7644 §3.3
        <7644#section-3.3>`.

        :param resource: The resource to create
        :param kwargs: Additional parameters passed to the underlying HTTP request
            library.

        :return:
            - An :class:`~scim2_models.Error` object in case of error.
            - The created object as returned by the server in case of success.
        """

        self.check_resource_type(resource.__class__)
        url = self.resource_endpoint(resource.__class__)
        dump = resource.model_dump(scim_ctx=Context.RESOURCE_CREATION_REQUEST)
        response = self.client.post(url, json=dump, **kwargs)

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
        return self.check_response(
            response,
            expected_status_codes,
            resource.__class__,
            scim_ctx=Context.RESOURCE_CREATION_RESPONSE,
        )

    def query(
        self,
        resource_type: Type,
        id: Optional[str] = None,
        search_request: Optional[SearchRequest] = None,
        **kwargs,
    ) -> Union[AnyResource, ListResponse[AnyResource], Error]:
        """Perform a GET request to read resources, as defined in :rfc:`RFC7644
        §3.4.2 <7644#section-3.4.2>`.

        - If `id` is not :data:`None`, the resource with the exact id will be reached.
        - If `id` is :data:`None`, all the resources with the given type will be reached.

        :param resource_type: A :class:`~scim2_models.Resource` subtype or :data:`None`
        :param id: The SCIM id of an object to get, or :data:`None`
        :param search_request: An object detailing the search query parameters.
        :param kwargs: Additional parameters passed to the underlying HTTP request library.

        :return:
            - A :class:`~scim2_models.Error` object in case of error.
            - A `resource_type` object in case of success if `id` is not :data:`None`
            - A :class:`~scim2_models.ListResponse[resource_type]` object in case of success if `id` is :data:`None`
        """

        self.check_resource_type(resource_type)
        payload = (
            search_request.model_dump(
                exclude_unset=True, scim_ctx=Context.RESOURCE_QUERY_REQUEST, attributes=search_request.attributes, excluded_attributes=search_request.excluded_attributes
            )
            if search_request
            else None
        )

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
        response = self.client.get(url, params=payload, **kwargs)
        return self.check_response(
            response,
            expected_status_codes,
            expected_type,
            scim_ctx=Context.RESOURCE_QUERY_RESPONSE,
        )

    def query_all(
        self,
        search_request: Optional[SearchRequest] = None,
        **kwargs,
    ) -> Union[AnyResource, ListResponse[AnyResource], Error]:
        """Perform a GET request to read all available resources, as defined in
        :rfc:`RFC7644 §3.4.2.1 <7644#section-3.4.2.1>`.

        :param search_request: An object detailing the search query parameters.
        :param kwargs: Additional parameters passed to the underlying
            HTTP request library.

        :return:
            - A :class:`~scim2_models.Error` object in case of error.
            - A :class:`~scim2_models.ListResponse[resource_type]` object in case of success.
        """

        # A query against a server root indicates that all resources within the
        # server SHALL be included, subject to filtering.
        # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.4.2.1

        payload = (
            search_request.model_dump(
                exclude_unset=True, scim_ctx=Context.RESOURCE_QUERY_REQUEST
            )
            if search_request
            else None
        )
        response = self.client.get("/", params=payload)

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
            response,
            expected_status_codes,
            ListResponse[Union[self.resource_types]],
            scim_ctx=Context.RESOURCE_QUERY_RESPONSE,
        )

    def search(
        self,
        search_request: Optional[SearchRequest] = None,
        **kwargs,
    ) -> Union[AnyResource, ListResponse[AnyResource], Error]:
        """Perform a POST search request to read all available resources, as
        defined in :rfc:`RFC7644 §3.4.3 <7644#section-3.4.3>`.

        :param resource_types: Resource type or union of types expected
            to be read from the response.
        :param search_request: An object detailing the search query parameters.
        :param kwargs: Additional parameters passed to the underlying
            HTTP request library.

        :return:
            - A :class:`~scim2_models.Error` object in case of error.
            - A :class:`~scim2_models.ListResponse[resource_type]` object in case of success.
        """

        payload = (
            search_request.model_dump(
                exclude_unset=True, scim_ctx=Context.RESOURCE_QUERY_RESPONSE
            )
            if search_request
            else None
        )
        response = self.client.post("/.search", params=payload)

        expected_status_codes = [
            # Resource querying HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644#section-3.4.3
            200,
            # Default HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.12
            307,
            308,
            400,
            401,
            403,
            404,
            409,
            413,
            500,
            501,
        ]
        return self.check_response(
            response,
            expected_status_codes,
            ListResponse[Union[self.resource_types]],
            scim_ctx=Context.RESOURCE_QUERY_RESPONSE,
        )

    def delete(self, resource_type: Type, id: str, **kwargs) -> Optional[Error]:
        """Perform a DELETE request to create, as defined in :rfc:`RFC7644 §3.6
        <7644#section-3.6>`.

        :param kwargs: Additional parameters passed to the underlying
            HTTP request library.

        :return:
            - A :class:`~scim2_models.Error` object in case of error.
            - :data:`None` in case of success.
        """

        self.check_resource_type(resource_type)
        url = self.resource_endpoint(resource_type) + f"/{id}"
        response = self.client.delete(url, **kwargs)

        expected_status_codes = [
            # Resource deletion HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644#section-3.6
            204,
            # Default HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.12
            307,
            308,
            400,
            401,
            403,
            404,
            412,
            500,
            501,
        ]
        return self.check_response(response, expected_status_codes)

    def replace(self, resource: AnyResource, **kwargs) -> Union[AnyResource, Error]:
        """Perform a PUT request to replace a resource, as defined in
        :rfc:`RFC7644 §3.5.1 <7644#section-3.5.1>`.

        :param resource: The new state of the resource to replace.
        :param kwargs: Additional parameters passed to the underlying
            HTTP request library.

        :return:
            - An :class:`~scim2_models.Error` object in case of error.
            - The updated object as returned by the server in case of success.
        """

        self.check_resource_type(resource.__class__)
        if not resource.id:
            raise Exception("Resource must have an id")

        dump = resource.model_dump(scim_ctx=Context.RESOURCE_REPLACEMENT_REQUEST)
        url = self.resource_endpoint(resource.__class__) + f"/{resource.id}"
        response = self.client.put(url, json=dump, **kwargs)

        expected_status_codes = [
            # Resource querying HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644#section-3.4.2
            200,
            # Default HTTP codes defined at:
            # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.12
            307,
            308,
            400,
            401,
            403,
            404,
            409,
            412,
            500,
            501,
        ]
        return self.check_response(
            response,
            expected_status_codes,
            resource.__class__,
            scim_ctx=Context.RESOURCE_REPLACEMENT_RESPONSE,
        )

    def modify(
        self, resource: AnyResource, op: PatchOp, **kwargs
    ) -> Optional[AnyResource]:
        raise NotImplementedError()
