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
import threading as _threading
import time as _time
import traceback as _traceback

from .httpserver import HttpServer

_log = _logging.getLogger("app")

class Application:
    def __init__(self, home, data_dir=None, http_port=8080):
        self.home = home
        self.data_dir = data_dir
        self.http_port = http_port

        if self.data_dir is None:
            self.data_dir = _os.path.join(self.home, "data")

        self.http_server = HttpServer(self, port=self.http_port)

        self.cleaner_thread = _BuildCleanerThread(self)

    def run(self):
        _logging.basicConfig(level=_logging.DEBUG)

        if not _os.path.exists(self.data_dir):
            _os.makedirs(self.data_dir)

        self.cleaner_thread.start()

        self.http_server.run()

class _BuildCleanerThread(_threading.Thread):
    def __init__(self, app):
        super().__init__()

        self.app = app
        self.daemon = True

    def run(self):
        while True:
            _time.sleep(1)

            try:
                self.clean_builds()
            except KeyboardInterrupt:
                raise
            except Exception:
                _traceback.print_exc()

    def clean_builds(self):
        _log.info("Cleaning builds")
        
        # builds/{repo}/{branch}/{build}

        #build_data = http_get(f"{stagger_service}/api/data")
        root_dir = _os.path.join(self.app.home, "builds")

        if not _os.path.exists(root_dir):
            _os.makedirs(root_dir)

        for repo_id in _os.listdir(root_dir):
            repo_dir = _os.path.join(root_dir, repo_id)

            for branch_id in _os.listdir(repo_dir):
                branch_dir = _os.path.join(repo_dir, branch_id)

                for build_id in _os.listdir(branch_dir):
                    build_dir = _os.path.join(branch_dir, build_id)

                    _log.info(f"XXX {build_dir}")

                    # if build_dir is newer than 1 day old
                    # or if build has an associated tag
                    # keep it

if __name__ == "__main__":
    app = Application(_os.getcwd())
    app.run()
