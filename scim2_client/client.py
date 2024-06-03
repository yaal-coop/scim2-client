import json
import json.decoder
from typing import Dict
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
from scim2_models import Resource
from scim2_models import SearchRequest
from scim2_models import ServiceProviderConfig

from .errors import SCIMClientError
from .errors import UnexpectedContentFormat
from .errors import UnexpectedContentType
from .errors import UnexpectedStatusCode

BASE_HEADERS = {
    "Accept": "application/scim+json",
    "Content-Type": "application/scim+json",
}


class SCIMClient:
    """An object that perform SCIM requests and validate responses."""

    CREATION_RESPONSE_STATUS_CODES: List[int] = [
        201,
        409,
        307,
        308,
        400,
        401,
        403,
        404,
        500,
    ]
    """Resource creation HTTP codes defined at :rfc:`RFC7644 §3.3
    <7644#section-3.3>` and :rfc:`RFC7644 §3.12 <7644#section-3.12>`"""

    QUERY_RESPONSE_STATUS_CODES: List[int] = [200, 400, 307, 308, 401, 403, 404, 500]
    """Resource querying HTTP codes defined at :rfc:`RFC7644 §3.4.2
    <7644#section-3.4.2>` and :rfc:`RFC7644 §3.12 <7644#section-3.12>`"""

    SEARCH_RESPONSE_STATUS_CODES: List[int] = [
        200,
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
    """Resource querying HTTP codes defined at :rfc:`RFC7644 §3.4.3
    <7644#section-3.4.3>` and :rfc:`RFC7644 §3.12 <7644#section-3.12>`"""

    DELETION_RESPONSE_STATUS_CODES: List[int] = [
        204,
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
    """Resource deletion HTTP codes defined at :rfc:`RFC7644 §3.6
    <7644#section-3.6>` and :rfc:`RFC7644 §3.12 <7644#section-3.12>`"""

    REPLACEMENT_RESPONSE_STATUS_CODES: List[int] = [
        200,
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
    """Resource querying HTTP codes defined at :rfc:`RFC7644 §3.4.2
    <7644#section-3.4.2>` and :rfc:`RFC7644 §3.12 <7644#section-3.12>`"""

    def __init__(self, client: Client, resource_types: Optional[Tuple[Type]] = None):
        self.client = client
        self.resource_types = resource_types or ()

    def check_resource_type(self, resource_type):
        if resource_type not in self.resource_types:
            raise ValueError(f"Unknown resource type: '{resource_type}'")

    def resource_endpoint(self, resource_type: Type):
        # This one takes no final 's'
        if resource_type is ServiceProviderConfig:
            return "/ServiceProviderConfig"

        try:
            first_bracket_index = resource_type.__name__.index("[")
            root_name = resource_type.__name__[:first_bracket_index]
        except ValueError:
            root_name = resource_type.__name__
        return f"/{root_name}s"

    def check_response(
        self,
        response: Response,
        expected_status_codes: List[int],
        expected_type: Optional[Type] = None,
        scim_ctx: Optional[Context] = None,
    ):
        if expected_status_codes and response.status_code not in expected_status_codes:
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

        no_content_status_codes = [204, 205]
        if response.status_code in no_content_status_codes:
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
            try:
                return expected_type.model_validate(response_payload, scim_ctx=scim_ctx)
            except ValidationError as exc:
                exc.response_payload = response_payload
                raise exc

        return response_payload

    def create(
        self,
        resource: Union[AnyResource, Dict],
        check_request_payload: bool = True,
        check_response_payload: bool = True,
        check_status_code: bool = True,
        **kwargs,
    ) -> Union[AnyResource, Error, Dict]:
        """Perform a POST request to create, as defined in :rfc:`RFC7644 §3.3
        <7644#section-3.3>`.

        :param resource: The resource to create
            If is a :data:`dict`, the resource type will be guessed from the schema.
        :param check_request_payload: If :data:`False`,
            :code:`resource` is expected to be a dict that will be passed as-is in the request.
        :param check_response_payload: Whether to validate that the response payload is valid.
            If set, the raw payload will be returned.
        :param check_status_code: Whether to validate that the response status code is valid.
        :param kwargs: Additional parameters passed to the underlying HTTP request
            library.

        :return:
            - An :class:`~scim2_models.Error` object in case of error.
            - The created object as returned by the server in case of success and :code:`check_response_payload` is :data:`True`.
            - The created object payload as returned by the server in case of success and :code:`check_response_payload` is :data:`False`.

        .. code-block:: python
            :caption: Creation of a `User` resource

            from scim2_models import User

            request = User(user_name="bjensen@example.com")
            response = scim.create(request)
            # 'response' may be a User or an Error object

        .. tip::

            Check the :attr:`~scim2_models.Context.RESOURCE_CREATION_REQUEST`
            and :attr:`~scim2_models.Context.RESOURCE_CREATION_RESPONSE` contexts to understand
            which value will excluded from the request payload, and which values are expected in
            the response payload.
        """

        if not check_request_payload:
            payload = resource
            url = kwargs.pop("url", None)

        else:
            if isinstance(resource, Resource):
                resource_type = resource.__class__

            else:
                resource_type = Resource.get_by_payload(self.resource_types, resource)
                if not resource_type:
                    raise SCIMClientError(
                        None, "Cannot guess resource type from the payload"
                    )

                resource = resource_type.model_validate(resource)

            self.check_resource_type(resource_type)
            url = kwargs.pop("url", self.resource_endpoint(resource_type))
            payload = resource.model_dump(scim_ctx=Context.RESOURCE_CREATION_REQUEST)

        response = self.client.post(url, json=payload, **kwargs)

        return self.check_response(
            response,
            self.CREATION_RESPONSE_STATUS_CODES if check_status_code else None,
            resource.__class__
            if check_request_payload and check_response_payload
            else None,
            scim_ctx=Context.RESOURCE_CREATION_RESPONSE,
        )

    def query(
        self,
        resource_type: Type,
        id: Optional[str] = None,
        search_request: Optional[Union[SearchRequest, Dict]] = None,
        check_request_payload: bool = True,
        check_response_payload: bool = True,
        check_status_code: bool = True,
        **kwargs,
    ) -> Union[AnyResource, ListResponse[AnyResource], Error, Dict]:
        """Perform a GET request to read resources, as defined in :rfc:`RFC7644
        §3.4.2 <7644#section-3.4.2>`.

        - If `id` is not :data:`None`, the resource with the exact id will be reached.
        - If `id` is :data:`None`, all the resources with the given type will be reached.

        :param resource_type: A :class:`~scim2_models.Resource` subtype or :data:`None`
        :param id: The SCIM id of an object to get, or :data:`None`
        :param search_request: An object detailing the search query parameters.
        :param check_request_payload: If :data:`False`,
            :code:`search_request` is expected to be a dict that will be passed as-is in the request.
        :param check_response_payload: Whether to validate that the response payload is valid.
            If set, the raw payload will be returned.
        :param check_status_code: Whether to validate that the response status code is valid.
        :param kwargs: Additional parameters passed to the underlying HTTP request library.

        :return:
            - A :class:`~scim2_models.Error` object in case of error.
            - A `resource_type` object in case of success if `id` is not :data:`None`
            - A :class:`~scim2_models.ListResponse[resource_type]` object in case of success if `id` is :data:`None`

        .. code-block:: python
            :caption: Query of a `User` resource knowing its id

            from scim2_models import User

            response = scim.query(User, "my-user-id)
            # 'response' may be a User or an Error object

        .. code-block:: python
            :caption: Query of all the `User` resources filtering the ones with `userName` starts with `john`

            from scim2_models import User, SearchRequest

            req = SearchRequest(filter='filter=userName sw "john"')
            response = scim.query(User, search_request=search_request)
            # 'response' may be a ListResponse[User] or an Error object

        .. tip::

            Check the :attr:`~scim2_models.Context.RESOURCE_QUERY_REQUEST`
            and :attr:`~scim2_models.Context.RESOURCE_QUERY_RESPONSE` contexts to understand
            which value will excluded from the request payload, and which values are expected in
            the response payload.
        """

        self.check_resource_type(resource_type)
        if not check_request_payload:
            payload = search_request

        else:
            payload = (
                search_request.model_dump(
                    exclude_unset=True,
                    scim_ctx=Context.RESOURCE_QUERY_REQUEST,
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

        response = self.client.get(url, params=payload, **kwargs)
        return self.check_response(
            response,
            self.QUERY_RESPONSE_STATUS_CODES if check_status_code else None,
            expected_type if check_response_payload else None,
            scim_ctx=Context.RESOURCE_QUERY_RESPONSE,
        )

    def query_all(
        self,
        search_request: Optional[SearchRequest] = None,
        check_request_payload: bool = True,
        check_response_payload: bool = True,
        check_status_code: bool = True,
        **kwargs,
    ) -> Union[AnyResource, ListResponse[AnyResource], Error, Dict]:
        """Perform a GET request to read all available resources, as defined in
        :rfc:`RFC7644 §3.4.2.1 <7644#section-3.4.2.1>`.

        :param search_request: An object detailing the search query parameters.
        :param check_request_payload: If :data:`False`,
            :code:`search_request` is expected to be a dict that will be passed as-is in the request.
        :param check_response_payload: Whether to validate that the response payload is valid.
            If set, the raw payload will be returned.
        :param check_status_code: Whether to validate that the response status code is valid.
        :param kwargs: Additional parameters passed to the underlying
            HTTP request library.

        :return:
            - A :class:`~scim2_models.Error` object in case of error.
            - A :class:`~scim2_models.ListResponse[resource_type]` object in case of success.

        .. code-block:: python
            :caption: Query of all the resources filtering the ones with `id` contains with `admin`

            from scim2_models import User, SearchRequest

            req = SearchRequest(filter='filter=id co "john"')
            response = scim.query_all(search_request=search_request)
            # 'response' may be a ListResponse[User] or an Error object

        .. tip::

            Check the :attr:`~scim2_models.Context.RESOURCE_QUERY_REQUEST`
            and :attr:`~scim2_models.Context.RESOURCE_QUERY_RESPONSE` contexts to understand
            which value will excluded from the request payload, and which values are expected in
            the response payload.
        """

        # A query against a server root indicates that all resources within the
        # server SHALL be included, subject to filtering.
        # https://datatracker.ietf.org/doc/html/rfc7644.html#section-3.4.2.1

        if not check_request_payload:
            payload = search_request

        else:
            payload = (
                search_request.model_dump(
                    exclude_unset=True, scim_ctx=Context.RESOURCE_QUERY_REQUEST
                )
                if search_request
                else None
            )

        response = self.client.get("/", params=payload)

        return self.check_response(
            response,
            self.QUERY_RESPONSE_STATUS_CODES if check_status_code else None,
            ListResponse[Union[self.resource_types]]
            if check_response_payload
            else None,
            scim_ctx=Context.RESOURCE_QUERY_RESPONSE,
        )

    def search(
        self,
        search_request: Optional[SearchRequest] = None,
        check_request_payload: bool = True,
        check_response_payload: bool = True,
        check_status_code: bool = True,
        **kwargs,
    ) -> Union[AnyResource, ListResponse[AnyResource], Error, Dict]:
        """Perform a POST search request to read all available resources, as
        defined in :rfc:`RFC7644 §3.4.3 <7644#section-3.4.3>`.

        :param resource_types: Resource type or union of types expected
            to be read from the response.
        :param search_request: An object detailing the search query parameters.
        :param check_request_payload: If :data:`False`,
            :code:`search_request` is expected to be a dict that will be passed as-is in the request.
        :param check_response_payload: Whether to validate that the response payload is valid.
            If set, the raw payload will be returned.
        :param check_status_code: Whether to validate that the response status code is valid.
        :param kwargs: Additional parameters passed to the underlying
            HTTP request library.

        :return:
            - A :class:`~scim2_models.Error` object in case of error.
            - A :class:`~scim2_models.ListResponse[resource_type]` object in case of success.

        .. code-block:: python
            :caption: Searching for all the resources filtering the ones with `id` contains with `admin`

            from scim2_models import User, SearchRequest

            req = SearchRequest(filter='filter=id co "john"')
            response = scim.search(search_request=search_request)
            # 'response' may be a ListResponse[User] or an Error object

        .. tip::

            Check the :attr:`~scim2_models.Context.SEARCH_REQUEST`
            and :attr:`~scim2_models.Context.SEARCH_RESPONSE` contexts to understand
            which value will excluded from the request payload, and which values are expected in
            the response payload.
        """

        if not check_request_payload:
            payload = search_request

        else:
            payload = (
                search_request.model_dump(
                    exclude_unset=True, scim_ctx=Context.RESOURCE_QUERY_RESPONSE
                )
                if search_request
                else None
            )

        response = self.client.post("/.search", json=payload)

        return self.check_response(
            response,
            self.SEARCH_RESPONSE_STATUS_CODES if check_status_code else None,
            ListResponse[Union[self.resource_types]]
            if check_response_payload
            else None,
            scim_ctx=Context.RESOURCE_QUERY_RESPONSE,
        )

    def delete(
        self, resource_type: Type, id: str, check_status_code: bool = True, **kwargs
    ) -> Optional[Union[Error, Dict]]:
        """Perform a DELETE request to create, as defined in :rfc:`RFC7644 §3.6
        <7644#section-3.6>`.

        :param check_status_code: Whether to validate that the response status code is valid.
        :param kwargs: Additional parameters passed to the underlying
            HTTP request library.

        .. code-block:: python
            :caption: Deleting an `User` which `id` is `foobar`

            from scim2_models import User, SearchRequest

            response = scim.delete(User, "foobar")
            # 'response' may be None, or an Error object

        :return:
            - A :class:`~scim2_models.Error` object in case of error.
            - :data:`None` in case of success.
        """

        self.check_resource_type(resource_type)
        url = self.resource_endpoint(resource_type) + f"/{id}"
        response = self.client.delete(url, **kwargs)

        return self.check_response(
            response, self.DELETION_RESPONSE_STATUS_CODES if check_status_code else None
        )

    def replace(
        self,
        resource: Union[AnyResource, Dict],
        check_request_payload: bool = True,
        check_response_payload: bool = True,
        check_status_code: bool = True,
        **kwargs,
    ) -> Union[AnyResource, Error, Dict]:
        """Perform a PUT request to replace a resource, as defined in
        :rfc:`RFC7644 §3.5.1 <7644#section-3.5.1>`.

        :param resource: The new resource to replace.
            If is a :data:`dict`, the resource type will be guessed from the schema.
        :param check_request_payload: If :data:`False`,
            :code:`resource` is expected to be a dict that will be passed as-is in the request.
        :param check_response_payload: Whether to validate that the response payload is valid.
            If set, the raw payload will be returned.
        :param check_status_code: Whether to validate that the response status code is valid.
        :param kwargs: Additional parameters passed to the underlying
            HTTP request library.

        :return:
            - An :class:`~scim2_models.Error` object in case of error.
            - The updated object as returned by the server in case of success.

        .. code-block:: python
            :caption: Replacement of a `User` resource

            from scim2_models import User

            user = scim.query(User, "my-used-id")
            user.display_name = "Fancy New Name"
            response = scim.update(user)
            # 'response' may be a User or an Error object

        .. tip::

            Check the :attr:`~scim2_models.Context.RESOURCE_REPLACEMENT_REQUEST`
            and :attr:`~scim2_models.Context.RESOURCE_REPLACEMENT_RESPONSE` contexts to understand
            which value will excluded from the request payload, and which values are expected in
            the response payload.
        """

        if not check_request_payload:
            payload = resource
            url = kwargs.pop("url", None)

        else:
            if isinstance(resource, Resource):
                resource_type = resource.__class__

            else:
                resource_type = Resource.get_by_payload(self.resource_types, resource)
                if not resource_type:
                    raise SCIMClientError(
                        None, "Cannot guess resource type from the payload"
                    )

                resource = resource_type.model_validate(resource)

            self.check_resource_type(resource_type)

            if not resource.id:
                raise SCIMClientError(None, "Resource must have an id")

            payload = resource.model_dump(scim_ctx=Context.RESOURCE_REPLACEMENT_REQUEST)
            url = kwargs.pop(
                "url", self.resource_endpoint(resource.__class__) + f"/{resource.id}"
            )

        response = self.client.put(url, json=payload, **kwargs)

        return self.check_response(
            response,
            self.REPLACEMENT_RESPONSE_STATUS_CODES if check_status_code else None,
            resource.__class__
            if check_request_payload and check_response_payload
            else None,
            scim_ctx=Context.RESOURCE_REPLACEMENT_RESPONSE,
        )

    def modify(
        self, resource: Union[AnyResource, Dict], op: PatchOp, **kwargs
    ) -> Optional[Union[AnyResource, Dict]]:
        raise NotImplementedError()
