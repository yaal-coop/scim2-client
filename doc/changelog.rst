Changelog
=========

[0.2.0] - 2024-09-01
---------------------

Added
^^^^^
- Replace :code:`check_status_code` parameter by :code:`expected_status_codes`.

Changed
^^^^^^^
- :code:`raise_scim_errors` is :data:`True` by default.

[0.1.11] - 2024-08-31
---------------------

Fixed
^^^^^
- Support for content-types with charset information. #18 #19

[0.1.10] - 2024-08-18
---------------------

Changed
^^^^^^^
- Bump to scim2-models 0.2.0.

[0.1.9] - 2024-06-30
--------------------

Changed
^^^^^^^
- Fix httpx dependency versions.

[0.1.8] - 2024-06-30
--------------------

Changed
^^^^^^^
- Lower the httpx dependency to 0.24.0

[0.1.7] - 2024-06-28
--------------------

Fixed
^^^^^
- Support for scim2-models 0.1.8

[0.1.6] - 2024-06-05
--------------------

Added
^^^^^
- :class:`~scim2_client.SCIMResponseErrorObject` implementation.

[0.1.5] - 2024-06-05
--------------------

Changed
^^^^^^^
- Merge :meth:`~scim2_client.SCIMClient.query` and :meth:`~scim2_client.SCIMClient.query_all`.

Added
^^^^^
- Implement :meth:`~scim2_client.SCIMClient.delete` `check_response_payload` attribute.
- :class:`~scim2_models.ServiceProviderConfig`, :class:`~scim2_models.ResourceType`
  and :class:`~scim2_models.Schema` are added to the default resource types list.
- Any custom URL can be used with all the :class:`~scim2_client.SCIMClient` methods.
- :class:`~scim2_client.ResponsePayloadValidationError` implementation.
- :class:`~scim2_client.RequestPayloadValidationError` implementation.
- :class:`~scim2_client.RequestNetworkError` implementation.

Fixed
^^^^^
- Endpoint guessing for :class:`~scim2_models.ServiceProviderConfig`.
- :class:`~scim2_models.ServiceProviderConfig` cannot have ids and are not returned in :class:`~scim2_models.ListResponse`.

[0.1.4] - 2024-06-03
--------------------

Fixed
^^^^^
- :meth:`~scim2_client.SCIMClient.resource_endpoint` could not correctly guess endpoints for resources with extensions.

[0.1.3] - 2024-06-03
--------------------

Added
^^^^^
- :meth:`~scim2_client.SCIMClient.create` and :meth:`~scim2_client.SCIMClient.replace` can guess resource types by their payloads.

[0.1.2] - 2024-06-02
--------------------

Added
^^^^^
- :code:`check_response_payload` and :code:`check_status_code` parameters for all methods.
- :code:`check_request_payload` parameter for all methods.

[0.1.1] - 2024-06-01
--------------------

Added
^^^^^
- Use of scim2-models request contexts to produce adequate payloads.

[0.1.0] - 2024-06-01
--------------------

Added
^^^^^
- Initial release
