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
        message="Unexpected response status code",
        **kwargs,
    ):
        super().__init__(response, message, *args, **kwargs)


class UnexpectedContentType(SCIMClientError):
    def __init__(
        self,
        response: Response,
        *args,
        message="Unexpected response content type",
        **kwargs,
    ):
        super().__init__(response, message, *args, **kwargs)


class UnexpectedContentFormat(SCIMClientError):
    def __init__(
        self,
        response: Response,
        *args,
        message="Unexpected response content type",
        **kwargs,
    ):
        super().__init__(response, message, *args, **kwargs)
