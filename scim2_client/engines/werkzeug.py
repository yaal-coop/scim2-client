from contextlib import contextmanager
from typing import Optional
from typing import Union
from urllib.parse import urlencode

from scim2_models import AnyResource
from scim2_models import Context
from scim2_models import Error
from scim2_models import ListResponse
from scim2_models import Resource
from scim2_models import SearchRequest
from werkzeug.test import Client

from scim2_client.client import BaseSCIMClient
from scim2_client.errors import SCIMClientError


@contextmanager
def handle_response_error(response):
    try:
        yield

    except SCIMClientError as exc:
        exc.source = response
        raise exc


class TestSCIMClient(BaseSCIMClient):
    """A client based on :class:`Werkzeug test Client <werkzeug.test.Client>` for application development purposes.

    This is helpful for developers of SCIM servers.
    This client avoids to perform real HTTP requests and directly execute the server code instead.
    This allows to dynamically catch the exceptions if something gets wrong.

    :param client: A WSGI application instance that will be used to send requests.
    :param scim_prefix: The scim root endpoint in the application.
    :param resource_models: The client resource types.

    .. code-block:: python

        from scim2_client.engines.werkzeug import TestSCIMClient
        from scim2_models import User, Group

        testclient = TestSCIMClient(app=scim_provider, resource_models=(User, Group))

        request_user = User(user_name="foo", display_name="bar")
        response_user = scim_client.create(request_user)
        assert response_user.user_name == "foo"
    """

    def __init__(
        self,
        app,
        scim_prefix: str = "",
        resource_models: Optional[tuple[type[Resource]]] = None,
    ):
        super().__init__(resource_models=resource_models)
        self.client = Client(app)
        self.scim_prefix = scim_prefix

    def make_url(self, url: str) -> str:
        prefix = (
            self.scim_prefix[:-1]
            if self.scim_prefix.endswith("/")
            else self.scim_prefix
        )
        return f"{prefix}{url}"

    def create(
        self,
        resource: Union[AnyResource, dict],
        check_request_payload: bool = True,
        check_response_payload: bool = True,
        expected_status_codes: Optional[
            list[int]
        ] = BaseSCIMClient.CREATION_RESPONSE_STATUS_CODES,
        raise_scim_errors: bool = True,
        **kwargs,
    ) -> Union[AnyResource, Error, dict]:
        url, payload, expected_types, request_kwargs = self.prepare_create_request(
            resource=resource,
            check_request_payload=check_request_payload,
            check_response_payload=check_response_payload,
            expected_status_codes=expected_status_codes,
            raise_scim_errors=raise_scim_errors,
            **kwargs,
        )

        response = self.client.post(self.make_url(url), json=payload, **request_kwargs)

        with handle_response_error(payload):
            return self.check_response(
                payload=response.json if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=expected_status_codes,
                expected_types=expected_types,
                check_response_payload=check_response_payload,
                raise_scim_errors=raise_scim_errors,
                scim_ctx=Context.RESOURCE_CREATION_RESPONSE,
            )

    def query(
        self,
        resource_model: Optional[type[Resource]] = None,
        id: Optional[str] = None,
        search_request: Optional[Union[SearchRequest, dict]] = None,
        check_request_payload: bool = True,
        check_response_payload: bool = True,
        expected_status_codes: Optional[
            list[int]
        ] = BaseSCIMClient.QUERY_RESPONSE_STATUS_CODES,
        raise_scim_errors: bool = True,
        **kwargs,
    ):
        url, payload, expected_types, request_kwargs = self.prepare_query_request(
            resource_model=resource_model,
            id=id,
            search_request=search_request,
            check_request_payload=check_request_payload,
            check_response_payload=check_response_payload,
            expected_status_codes=expected_status_codes,
            raise_scim_errors=raise_scim_errors,
            **kwargs,
        )

        query_string = urlencode(payload, doseq=False) if payload else None
        response = self.client.get(
            self.make_url(url), query_string=query_string, **request_kwargs
        )

        with handle_response_error(payload):
            return self.check_response(
                payload=response.json if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=expected_status_codes,
                expected_types=expected_types,
                check_response_payload=check_response_payload,
                raise_scim_errors=raise_scim_errors,
                scim_ctx=Context.RESOURCE_QUERY_RESPONSE,
            )

    def search(
        self,
        search_request: Optional[SearchRequest] = None,
        check_request_payload: bool = True,
        check_response_payload: bool = True,
        expected_status_codes: Optional[
            list[int]
        ] = BaseSCIMClient.SEARCH_RESPONSE_STATUS_CODES,
        raise_scim_errors: bool = True,
        **kwargs,
    ) -> Union[AnyResource, ListResponse[AnyResource], Error, dict]:
        url, payload, expected_types, request_kwargs = self.prepare_search_request(
            search_request=search_request,
            check_request_payload=check_request_payload,
            check_response_payload=check_response_payload,
            expected_status_codes=expected_status_codes,
            raise_scim_errors=raise_scim_errors,
            **kwargs,
        )

        response = self.client.post(self.make_url(url), json=payload, **request_kwargs)

        with handle_response_error(response):
            return self.check_response(
                payload=response.json if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=expected_status_codes,
                expected_types=expected_types,
                check_response_payload=check_response_payload,
                raise_scim_errors=raise_scim_errors,
                scim_ctx=Context.RESOURCE_QUERY_RESPONSE,
            )

    def delete(
        self,
        resource_model: type,
        id: str,
        check_response_payload: bool = True,
        expected_status_codes: Optional[
            list[int]
        ] = BaseSCIMClient.DELETION_RESPONSE_STATUS_CODES,
        raise_scim_errors: bool = True,
        **kwargs,
    ) -> Optional[Union[Error, dict]]:
        url, request_kwargs = self.prepare_delete_request(
            resource_model=resource_model,
            id=id,
            check_response_payload=check_response_payload,
            expected_status_codes=expected_status_codes,
            raise_scim_errors=raise_scim_errors,
            **kwargs,
        )

        response = self.client.delete(self.make_url(url), **request_kwargs)

        with handle_response_error(response):
            return self.check_response(
                payload=response.json if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=expected_status_codes,
                check_response_payload=check_response_payload,
                raise_scim_errors=raise_scim_errors,
            )

    def replace(
        self,
        resource: Union[AnyResource, dict],
        check_request_payload: bool = True,
        check_response_payload: bool = True,
        expected_status_codes: Optional[
            list[int]
        ] = BaseSCIMClient.REPLACEMENT_RESPONSE_STATUS_CODES,
        raise_scim_errors: bool = True,
        **kwargs,
    ) -> Union[AnyResource, Error, dict]:
        url, payload, expected_types, request_kwargs = self.prepare_replace_request(
            resource=resource,
            check_request_payload=check_request_payload,
            check_response_payload=check_response_payload,
            expected_status_codes=expected_status_codes,
            raise_scim_errors=raise_scim_errors,
            **kwargs,
        )

        response = self.client.put(self.make_url(url), json=payload, **request_kwargs)

        with handle_response_error(response):
            return self.check_response(
                payload=response.json if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=expected_status_codes,
                expected_types=expected_types,
                check_response_payload=check_response_payload,
                raise_scim_errors=raise_scim_errors,
                scim_ctx=Context.RESOURCE_REPLACEMENT_RESPONSE,
            )
