from httpx import Response


class SCIMClientError(Exception):
    """Base exception for scim2-client."""

    def __init__(self, response: Response, *args, **kwargs):
        self.response = response
        super().__init__(*args, **kwargs)


class UnexpectedStatusCode(SCIMClientError):
    """Error raised when a server returned an unexpected status code for a
    given :class:`~scim2_models.Context`."""

    def __init__(
        self,
        response: Response,
        *args,
        **kwargs,
    ):
        message = kwargs.pop(
            "message", f"Unexpected response status code: {response.status_code}"
        )
        super().__init__(response, message, *args, **kwargs)


class UnexpectedContentType(SCIMClientError):
    """Error raised when a server returned an unexpected `Content-Type` header
    in a response."""

    def __init__(
        self,
        response: Response,
        *args,
        **kwargs,
    ):
        content_type = response.headers.get("content-type", "")
        message = kwargs.pop("message", f"Unexpected content type: {content_type}")
        super().__init__(response, message, *args, **kwargs)


class UnexpectedContentFormat(SCIMClientError):
    """Error raised when a server returned a response in a non-JSON format."""

    def __init__(
        self,
        response: Response,
        *args,
        **kwargs,
    ):
        message = kwargs.pop("message", "Unexpected response content format")
        super().__init__(response, message, *args, **kwargs)
