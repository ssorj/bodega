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
import shutil as _shutil
import uuid as _uuid

from brbn import *

_log = _logging.getLogger("httpserver")

class HttpServer(Server):
    def __init__(self, app, host="", port=8080):
        super().__init__(app, host=host, port=port)

        self.add_route("/{repo_id}/{branch_id}/{build_id}",
                       endpoint=BuildHandler, methods=["DELETE"])
        self.add_route("/{repo_id}/{branch_id}/{build_id}/{path:path}",
                       endpoint=BuildFileHandler, methods=["PUT", "HEAD", "GET"])
        self.add_route("/{path:path}", endpoint=DirectoryHandler, methods=["GET"])

class DirectoryHandler(Handler):
    async def process(self, request):
        path = request.path_params["path"]

        if not _os.path.isdir(path):
            raise BadRequestError("Path is not a directory")

        return path

    async def render(self, request, path):
        return DirectoryIndexResponse(path)

class BuildHandler(Handler):
    async def process(self, request):
        repo_id = request.path_params["repo_id"]
        branch_id = request.path_params["branch_id"]
        build_id = request.path_params["build_id"]

        build_path = f"{request.app.home}/builds/{repo_id}/{branch_id}/{build_id}"

        if request.method == "DELETE":
            _shutil.rmtree(build_path, ignore_errors=True)

class BuildFileHandler(Handler):
    async def process(self, request):
        repo_id = request.path_params["repo_id"]
        branch_id = request.path_params["branch_id"]
        build_id = request.path_params["build_id"]
        path = request.path_params["path"]

        file_path = f"{request.app.home}/builds/{repo_id}/{branch_id}/{build_id}/{path}"

        if request.method == "PUT":
            if file_path.endswith("/"):
                raise BadRequestError("PUT of a directory is not supported")

            temp_path = f"{file_path}.{_unique_id(4)}.temp"
            dir_path, _ = _os.path.split(temp_path)

            if not _os.path.exists(dir_path):
                _os.makedirs(dir_path)

            with open(temp_path, "wb") as f:
                async for chunk in request.stream():
                    f.write(chunk)

            _os.rename(temp_path, file_path)

        # if request.method == "GET":
        #     print(111, file_path)
        #     if not _os.path.exists(file_path):
        #         raise NotFoundError(f"{file_path} does not exist")

        return file_path

    async def render(self, request, path):
        if request.method == "PUT":
            return OkResponse()

        assert path is not None

        if request.method == "GET":
            if _os.path.isfile(path):
                return FileResponse(path)
            elif _os.path.isdir(path):
                return DirectoryIndexResponse(path)

# Length in bytes, renders twice as long in hex
def _unique_id(length=16):
    assert length >= 1
    assert length <= 16

    uuid_bytes = _uuid.uuid4().bytes
    uuid_bytes = uuid_bytes[:length]

    return _binascii.hexlify(uuid_bytes).decode("utf-8")
