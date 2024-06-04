Tutorial
--------

Initialization
==============

scim2-client depends on `httpx <https://github.com/encode/httpx>`_ to perform network requests.
As a start you will need to instantiate a httpx :code:`Client` object that you can parameter as your will, and then pass it to a :class:`~scim2_client.SCIMClient` object.
In addition to your SCIM server root endpoint, you will probably want to provide some authorization headers:

.. code-block:: python

    from httpx import Client
    from scim2_models import User, EnterpriseUserUser, Group
    from scim2_client import SCIMClient

    client = Client(base_url="https://auth.example/scim/v2", headers={"Authorization": "Bearer foobar"})
    scim = SCIMClient(client, resource_types=(User[EnterpriseUser], Group))

You need to give to indicate to :class:`~scim2_client.SCIMClient` all the different :class:`~scim2_models.Resource` types that you will need to manipulate with the :code:`resource_types` parameter.
This is needed so scim2-client will be able to guess which resource type to instante when an arbitrary payload is met.

.. todo::

    We plan to implement the automatic discovery of SCIM server resources,
    so they can dynamically be used without explicitly passing them with the :code:`resource_types` parameter.

Performing actions
==================

scim2-client allows your application to interact with a SCIM server as described in :rfc:`RFC7644 §3 <7644#section-3>`, so you can read and manage the resources.
The following actions are available:

- :meth:`~scim2_client.SCIMClient.create`
- :meth:`~scim2_client.SCIMClient.query`
- :meth:`~scim2_client.SCIMClient.replace`
- :meth:`~scim2_client.SCIMClient.delete`
- :meth:`~scim2_client.SCIMClient.search`

Have a look at the :doc:`reference` to see usage examples and the exhaustive set of parameters, but generally it looks like this:

.. code-block:: python

    from scim2_models import Error

    request = User(user_name="bjensen@example.com")
    response = scim.create(request)
    if isinstance(response, Error):
        raise SomethingIsWrong(response.detail)

    return f"User {user.id} have been created!"

.. note::

    PATCH modification and bulk operation request are not yet implement,
    but :doc:`any help is welcome! <contributing>`

Request and response validation
===============================

By default, the data passed to the :class:`~scim2_client.SCIMClient` as well as the server response will be validated against the SCIM specifications, and will raise an error if they don't respect them.
However sometimes you want to accept invalid inputs and outputs.
To achieve this, all the methods provide the following parameters, all are :data:`True` by default:

- :code:`check_request_payload`:
  If :data:`True` a :class:`~pydantic.ValidationError` will be raised if the input does not respect the SCIM standard.
  If :data:`False`, input is expected to be a :data:`dict` that will be passed as-is in the request.
- :code:`check_response_payload`:
  If :data:`True` a :class:`~pydantic.ValidationError` will be raised if the server response does not respect the SCIM standard.
  If :data:`False` the server response is returned as-is.
- :code:`check_status_code`: Whether to validate that the response status code is valid.
  If :data:`True` and an unexpected status code is returned, a :class:`~scim2_client.errors.UnexpectedStatusCode` exception is raised.

.. tip::

   Check the request :class:`Contexts <scim2_models.Context>` to understand
   which value will excluded from the request payload, and which values are
   expected in the response payload.

Additional request parameters
=============================

Any additional parameter will be passed to the underlying httpx methods.
This can be usefull if you need to explicitly pass a certain URL for example:

.. code-block:: python

   scim.query(url="/User/i-know-what-im-doing")
