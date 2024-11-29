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

from scim2_client.client import BaseSyncSCIMClient
from scim2_client.errors import SCIMClientError


@contextmanager
def handle_response_error(response):
    try:
        yield

    except SCIMClientError as exc:
        exc.source = response
        raise exc


class TestSCIMClient(BaseSyncSCIMClient):
    """A client based on :class:`Werkzeug test Client <werkzeug.test.Client>` for application development purposes.

    This is helpful for developers of SCIM servers.
    This client avoids to perform real HTTP requests and directly execute the server code instead.
    This allows to dynamically catch the exceptions if something gets wrong.

    :param client: A WSGI application instance that will be used to send requests.
    :param scim_prefix: The scim root endpoint in the application.
    :param resource_models: A tuple of :class:`~scim2_models.Resource` types expected to be handled by the SCIM client.
        If a request payload describe a resource that is not in this list, an exception will be raised.

    .. code-block:: python

        from scim2_client.engines.werkzeug import TestSCIMClient
        from scim2_models import User, Group

        scim_provider = myapp.create_app()
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

    def make_url(self, url: Optional[str]) -> str:
        prefix = (
            self.scim_prefix[:-1]
            if self.scim_prefix.endswith("/")
            else self.scim_prefix
        )
        return f"{prefix}{url or ''}"

    def create(
        self,
        resource: Union[AnyResource, dict],
        check_request_payload: bool = True,
        check_response_payload: bool = True,
        expected_status_codes: Optional[
            list[int]
        ] = BaseSyncSCIMClient.CREATION_RESPONSE_STATUS_CODES,
        raise_scim_errors: bool = True,
        **kwargs,
    ) -> Union[AnyResource, Error, dict]:
        req = self.prepare_create_request(
            resource=resource,
            check_request_payload=check_request_payload,
            expected_status_codes=expected_status_codes,
            raise_scim_errors=raise_scim_errors,
            **kwargs,
        )

        response = self.client.post(
            self.make_url(req.url), json=req.payload, **req.request_kwargs
        )

        with handle_response_error(req.payload):
            return self.check_response(
                payload=response.json if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=req.expected_status_codes,
                expected_types=req.expected_types,
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
        ] = BaseSyncSCIMClient.QUERY_RESPONSE_STATUS_CODES,
        raise_scim_errors: bool = True,
        **kwargs,
    ):
        req = self.prepare_query_request(
            resource_model=resource_model,
            id=id,
            search_request=search_request,
            check_request_payload=check_request_payload,
            expected_status_codes=expected_status_codes,
            raise_scim_errors=raise_scim_errors,
            **kwargs,
        )

        query_string = urlencode(req.payload, doseq=False) if req.payload else None
        response = self.client.get(
            self.make_url(req.url), query_string=query_string, **req.request_kwargs
        )

        with handle_response_error(req.payload):
            return self.check_response(
                payload=response.json if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=req.expected_status_codes,
                expected_types=req.expected_types,
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
        ] = BaseSyncSCIMClient.SEARCH_RESPONSE_STATUS_CODES,
        raise_scim_errors: bool = True,
        **kwargs,
    ) -> Union[AnyResource, ListResponse[AnyResource], Error, dict]:
        req = self.prepare_search_request(
            search_request=search_request,
            check_request_payload=check_request_payload,
            expected_status_codes=expected_status_codes,
            raise_scim_errors=raise_scim_errors,
            **kwargs,
        )

        response = self.client.post(
            self.make_url(req.url), json=req.payload, **req.request_kwargs
        )

        with handle_response_error(response):
            return self.check_response(
                payload=response.json if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=req.expected_status_codes,
                expected_types=req.expected_types,
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
        ] = BaseSyncSCIMClient.DELETION_RESPONSE_STATUS_CODES,
        raise_scim_errors: bool = True,
        **kwargs,
    ) -> Optional[Union[Error, dict]]:
        req = self.prepare_delete_request(
            resource_model=resource_model,
            id=id,
            expected_status_codes=expected_status_codes,
            raise_scim_errors=raise_scim_errors,
            **kwargs,
        )

        response = self.client.delete(self.make_url(req.url), **req.request_kwargs)

        with handle_response_error(response):
            return self.check_response(
                payload=response.json if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=req.expected_status_codes,
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
        ] = BaseSyncSCIMClient.REPLACEMENT_RESPONSE_STATUS_CODES,
        raise_scim_errors: bool = True,
        **kwargs,
    ) -> Union[AnyResource, Error, dict]:
        req = self.prepare_replace_request(
            resource=resource,
            check_request_payload=check_request_payload,
            expected_status_codes=expected_status_codes,
            raise_scim_errors=raise_scim_errors,
            **kwargs,
        )

        response = self.client.put(
            self.make_url(req.url), json=req.payload, **req.request_kwargs
        )

        with handle_response_error(response):
            return self.check_response(
                payload=response.json if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=req.expected_status_codes,
                expected_types=req.expected_types,
                check_response_payload=check_response_payload,
                raise_scim_errors=raise_scim_errors,
                scim_ctx=Context.RESOURCE_REPLACEMENT_RESPONSE,
            )
