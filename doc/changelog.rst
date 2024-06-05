Changelog
=========

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
