from httpx import Response


class SCIMClientError(Exception):
    def __init__(self, response: Response, *args, **kwargs):
        self.response = response
        super().__init__(*args, **kwargs)


class UnexpectedStatusCode(SCIMClientError):
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
    def __init__(
        self,
        response: Response,
        *args,
        **kwargs,
    ):
        message = kwargs.pop("message", "Unexpected response content format")
        super().__init__(response, message, *args, **kwargs)
