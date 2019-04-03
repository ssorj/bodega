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
import uuid as _uuid

from brbn import *

_log = _logging.getLogger("httpserver")

class HttpServer(Server):
    def __init__(self, app, host="", port=8080):
        super().__init__(app, host=host, port=port)

        self.add_route("/builds/{repo_id}/{branch_id}/{build_id}",
                       endpoint=BuildHandler, methods=["GET", "HEAD"])

        self.add_static_files("", _os.path.join(app.home, "static"))

class WebAppHandler(Handler):
    _etag = str(_uuid.uuid4())

    def etag(self, request, obj):
        return self._etag

    async def render(self, request, obj):
        return FileResponse(path=_os.path.join(request.app.home, "static", "index.html"))

class BuildHandler(Handler):
    async def process(self, request):
        repo_id = request.path_params["repo_id"]
        branch_id = request.path_params["branch_id"]
        build_id = request.path_params["build_id"]

        # if request.method == "PUT":
        #     build_data = await request.json()
        #     build = model.put_build(repo_id, branch_id, build_id, build_data)
        #     return build

        # if request.method == "DELETE":
        #     model.delete_build(repo_id, branch_id, build_id)
        #     return

        return repo_id, branch_id, build_id

    async def render(self, request, obj):
        if request.method in ("PUT", "DELETE"):
            return OkResponse()

        assert obj is not None

        return JsonResponse(obj)
