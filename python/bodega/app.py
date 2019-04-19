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

import fortworth as _fortworth
import logging as _logging
import os as _os
import requests as _requests
import shutil as _shutil
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

        self.cleaner_thread = _BuildCleanerThread(self)
        self.http_server = HttpServer(self, port=self.http_port)

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
            _time.sleep(60)

            try:
                self.clean_builds()
            except KeyboardInterrupt:
                raise
            except Exception:
                _traceback.print_exc()

    def clean_builds(self):
        _log.info("Cleaning builds")

        data = _fortworth.stagger_get_data()
        root_dir = _os.path.join(self.app.home, "builds")

        if not _os.path.exists(root_dir):
            _os.makedirs(root_dir)

        for repo_id in _os.listdir(root_dir):
            repo_dir = _os.path.join(root_dir, repo_id)

            for branch_id in _os.listdir(repo_dir):
                branch_dir = _os.path.join(repo_dir, branch_id)

                for build_id in _os.listdir(branch_dir):
                    build_dir = _os.path.join(branch_dir, build_id)
                    fq_build_id = f"{repo_id}/{branch_id}/{build_id}"

                    _log.info(f"Considering build {fq_build_id} for deletion")

                    if _time.time() - _os.path.getmtime(build_dir) < 60 * 60:
                        _log.info("  The build was recently added; leaving it")
                        continue
                    else:
                        _log.info("  The build is old enough to go to the next check")

                    try:
                        tags = data["repos"][repo_id]["branches"][branch_id]["tags"]
                    except KeyError:
                        _log.info(f"  The build has no tags (1); deleting it")
                        _shutil.rmtree(build_dir, ignore_errors=True)
                        continue

                    for key, value in tags.items():
                        if value.get("build_id") == build_id:
                            _log.info("  The build has a tag; leaving it")
                            break
                    else:
                        _log.info("  The build has no tags (2); deleting it")
                        _shutil.rmtree(build_dir, ignore_errors=True)

if __name__ == "__main__":
    app = Application(_os.getcwd())
    app.run()
