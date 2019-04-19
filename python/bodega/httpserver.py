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
    async def handle(self, request):
        request_path = request.path_params["path"]
        fs_path = _os.path.join(request.app.builds_dir, request_path)
        fs_path = _os.path.normpath(fs_path)

        if not fs_path.startswith(request.app.builds_dir):
            return BadRequestResponse("Requested path not under the builds directory")

        if not _os.path.exists(fs_path):
            return NotFoundResponse()

        return DirectoryIndexResponse(request.app.builds_dir, request_path)

class BuildFileHandler(Handler):
    async def handle(self, request):
        repo_id = request.path_params["repo_id"]
        branch_id = request.path_params["branch_id"]
        build_id = request.path_params["build_id"]
        request_path = request.path_params["path"]

        build_dir = _os.path.join(request.app.builds_dir, repo_id, branch_id, build_id)
        fs_path = _os.path.join(build_dir, request_path)
        fs_path = _os.path.normpath(fs_path)

        if not fs_path.startswith(build_dir):
            return BadRequestResponse("Requested path not under the build directory")

        if request.method == "PUT":
            if fs_path.endswith("/"):
                return BadRequestResponse("PUT of a directory is not supported")

            temp_path = f"{fs_path}.{_uuid.uuid4()}.temp"
            dir_path, _ = _os.path.split(temp_path)

            if not _os.path.exists(dir_path):
                _os.makedirs(dir_path)

            with open(temp_path, "wb") as f:
                async for chunk in request.stream():
                    f.write(chunk)

            _os.rename(temp_path, fs_path)

            return OkResponse()

        if request.method == "GET":
            if not _os.path.exists(fs_path):
                return NotFoundResponse()

            if _os.path.isfile(fs_path):
                return FileResponse(fs_path)
            elif _os.path.isdir(fs_path):
                request_path = _os.path.join(repo_id, branch_id, build_id, request_path)
                return DirectoryIndexResponse(request.app.builds_dir, request_path)
            else:
                raise Exception()
