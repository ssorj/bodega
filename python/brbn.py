#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import json.decoder as _json_decoder
import logging as _logging
import os as _os
import starlette.requests as _requests
import starlette.routing as _routing
import starlette.staticfiles as _staticfiles
import traceback as _traceback
import uuid as _uuid
import uvicorn as _uvicorn

from starlette.responses import *

_log = _logging.getLogger("brbn")

class Server:
    def __init__(self, app, host="", port=8080):
        self.app = app
        self.host = host
        self.port = port

        self.router = Router(self.app)

    def add_route(self, *args, **kwargs):
        self.router.add_route(*args, **kwargs)

    def add_static_files(self, path, dir):
        self.router.mount(path, app=_staticfiles.StaticFiles(directory=dir))

    def run(self):
        _uvicorn.run(self.router, host=self.host, port=self.port, log_level="info")

class Router(_routing.Router):
    def __init__(self, app):
        super().__init__()
        self.app = app

    def __call__(self, scope):
        scope["app"] = self.app
        return super().__call__(scope)

class Request(_requests.Request):
    @property
    def app(self):
        return self["app"]

class Handler:
    def __init__(self, scope):
        self.scope = scope

    async def __call__(self, receive, send):
        request = Request(self.scope, receive)
        response = None

        try:
            obj = await self.process(request)
        except ProcessingException as e:
            response = e.response
        except _json_decoder.JSONDecodeError as e:
            # XXX Make this a processing exception
            response = BadJsonResponse(e)
        except Exception as e:
            response = ServerErrorResponse(e)

        if response is not None:
            return await response(receive, send)

        server_etag = self.etag(request, obj)

        if server_etag is not None:
            server_etag = f'"{server_etag}"'
            client_etag = request.headers.get("If-None-Match")

            print(111, server_etag)
            print(222, client_etag)

            if client_etag == server_etag:
                response = NotModifiedResponse()

        if request.method == "HEAD":
            response = Response("")

        if response is None:
            response = await self.render(request, obj)

        assert response is not None

        if server_etag is not None:
            response.headers["ETag"] = server_etag

        await response(receive, send)

    async def process(self, request):
        return None # obj

    def etag(self, request, obj):
        pass

    async def render(self, request, obj):
        return OkResponse()

class ProcessingException(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response

class Redirect(ProcessingException):
    def __init__(self, url):
        super().__init__(url, RedirectResponse(url))

class BadRequestError(ProcessingException):
    def __init__(self, message):
        super().__init__(message, BadRequestResponse(message))

class NotFoundError(ProcessingException):
    def __init__(self, message):
        super().__init__(message, NotFoundResponse(message))

class BadRequestResponse(PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Bad request: {exception}\n", 400)

class NotFoundResponse(PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Not found: {exception}\n", 404)

class NotModifiedResponse(PlainTextResponse):
    def __init__(self):
        super().__init__("Not modified\n", 304)

class ServerErrorResponse(PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Internal server error: {exception}\n", 500)
        _traceback.print_exc()

class BadJsonResponse(PlainTextResponse):
    def __init__(self, exception):
        super().__init__(f"Bad request: Failure decoding JSON: {exception}\n", 400)

class OkResponse(Response):
    def __init__(self):
        super().__init__("OK\n")

class HtmlResponse(HTMLResponse):
    pass

class JsonResponse(JSONResponse):
    pass

class CompressedJsonResponse(Response):
    def __init__(self, content):
        super().__init__(content, headers={"Content-Encoding": "gzip"}, media_type="application/json")

class DirectoryIndexResponse(HtmlResponse):
    def __init__(self, dir):
        super().__init__(self.make_index(dir))

    def make_index(self, dir):
        return """
<html>
  <head><title>XXX</title></head>
  <body>YYY</body>
</html>
"""
