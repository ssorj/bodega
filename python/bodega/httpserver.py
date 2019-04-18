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

import binascii as _binascii
import json.decoder as _json_decoder
import logging as _logging
import os as _os
import uuid as _uuid

from brbn import *

_log = _logging.getLogger("httpserver")

class HttpServer(Server):
    def __init__(self, app, host="", port=8080):
        super().__init__(app, host=host, port=port)

        self.add_route("/{repo_id}/{branch_id}/{build_id}/{path:path}",
                       endpoint=BuildFileHandler, methods=["PUT", "HEAD", "GET"])
        self.add_route("/{path:path}", endpoint=DirectoryHandler, methods=["GET"])

class DirectoryHandler(Handler):
    async def process(self, request):
        base_dir = f"{request.app.home}/builds"
        request_path = "/" + request.path_params["path"]
        fs_path = base_dir + request_path

        if not _os.path.isdir(fs_path):
            raise BadRequestError(f"No directory at {fs_path}")

        return base_dir, request_path

    async def render(self, request, paths):
        return DirectoryIndexResponse(*paths)

class BuildFileHandler(Handler):
    async def process(self, request):
        repo_id = request.path_params["repo_id"]
        branch_id = request.path_params["branch_id"]
        build_id = request.path_params["build_id"]
        file_path = request.path_params["path"]

        fs_path = f"{request.app.home}/builds/{repo_id}/{branch_id}/{build_id}/{file_path}"

        if request.method == "PUT":
            if fs_path.endswith("/"):
                raise BadRequestError("PUT of a directory is not supported")

            temp_path = f"{fs_path}.{_unique_id(4)}.temp"
            dir_path, _ = _os.path.split(temp_path)

            if not _os.path.exists(dir_path):
                _os.makedirs(dir_path)

            with open(temp_path, "wb") as f:
                async for chunk in request.stream():
                    f.write(chunk)

            _os.rename(temp_path, fs_path)

        if request.method == "GET":
            if not _os.path.exists(fs_path):
                raise NotFoundError(f"{fs_path} does not exist")

        return fs_path

    def etag(self, request, fs_path):
        pass # XXX

    async def render(self, request, fs_path):
        if request.method == "PUT":
            return OkResponse()

        assert fs_path is not None

        if request.method == "GET":
            if _os.path.isfile(fs_path):
                return FileResponse(fs_path)
            elif _os.path.isdir(fs_path):
                return DirectoryIndexResponse(fs_path)

# Length in bytes, renders twice as long in hex
def _unique_id(length=16):
    assert length >= 1
    assert length <= 16

    uuid_bytes = _uuid.uuid4().bytes
    uuid_bytes = uuid_bytes[:length]

    return _binascii.hexlify(uuid_bytes).decode("utf-8")
