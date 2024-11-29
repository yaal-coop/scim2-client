import json
import sys
from contextlib import contextmanager
from typing import Optional
from typing import Union

from httpx import Client
from httpx import RequestError
from httpx import Response
from scim2_models import AnyResource
from scim2_models import Context
from scim2_models import Error
from scim2_models import ListResponse
from scim2_models import Resource
from scim2_models import SearchRequest

from scim2_client.client import BaseSyncSCIMClient
from scim2_client.errors import RequestNetworkError
from scim2_client.errors import SCIMClientError
from scim2_client.errors import UnexpectedContentFormat


@contextmanager
def handle_request_error(payload=None):
    try:
        yield

    except RequestError as exc:
        scim_network_exc = RequestNetworkError(source=payload)
        if sys.version_info >= (3, 11):  # pragma: no cover
            scim_network_exc.add_note(str(exc))
        raise scim_network_exc from exc


@contextmanager
def handle_response_error(response: Response):
    try:
        yield

    except json.decoder.JSONDecodeError as exc:
        raise UnexpectedContentFormat(source=response) from exc

    except SCIMClientError as exc:
        exc.source = response
        raise exc


class SyncSCIMClient(BaseSyncSCIMClient):
    """Perform SCIM requests over the network and validate responses.

    :param client: A :class:`httpx.Client` instance that will be used to send requests.
    :param resource_models: A tuple of :class:`~scim2_models.Resource` types expected to be handled by the SCIM client.
        If a request payload describe a resource that is not in this list, an exception will be raised.
    """

    def __init__(
        self, client: Client, resource_models: Optional[tuple[type[Resource]]] = None
    ):
        super().__init__(resource_models=resource_models)
        self.client = client

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

        with handle_request_error(req.payload):
            response = self.client.post(req.url, json=req.payload, **req.request_kwargs)

        with handle_response_error(req.payload):
            return self.check_response(
                payload=response.json() if response.text else None,
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

        with handle_request_error(req.payload):
            response = self.client.get(
                req.url, params=req.payload, **req.request_kwargs
            )

        with handle_response_error(req.payload):
            return self.check_response(
                payload=response.json() if response.text else None,
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

        with handle_request_error(req.payload):
            response = self.client.post(req.url, json=req.payload, **req.request_kwargs)

        with handle_response_error(response):
            return self.check_response(
                payload=response.json() if response.text else None,
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

        with handle_request_error():
            response = self.client.delete(req.url, **req.request_kwargs)

        with handle_response_error(response):
            return self.check_response(
                payload=response.json() if response.text else None,
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

        with handle_request_error(req.payload):
            response = self.client.put(req.url, json=req.payload, **req.request_kwargs)

        with handle_response_error(response):
            return self.check_response(
                payload=response.json() if response.text else None,
                status_code=response.status_code,
                headers=response.headers,
                expected_status_codes=req.expected_status_codes,
                expected_types=req.expected_types,
                check_response_payload=check_response_payload,
                raise_scim_errors=raise_scim_errors,
                scim_ctx=Context.RESOURCE_REPLACEMENT_RESPONSE,
            )
