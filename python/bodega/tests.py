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

from commandant import TestSkipped
from plano import *

def open_test_session(session):
    enable_logging(level="error")
    session.test_timeout = 10

def _test_api(session, path, data):
    with TestServer() as server:
        url = f"{server.http_url}/{path}"

        try:
            head(url)
            assert False, "Expected this to 404"
        except CalledProcessError:
            pass

        test_data_dir = join(session.module.command.home, "test-data")
        test_build = join(test_data_dir, "build1")

        for file_path in find(test_build, "*"):
            relative_path = file_path[len(test_build):]
            put(f"{url}/{relative_path}", file_path)

        # get(url)
        # head(url)
        # delete(url)

def test_something(session):
    _test_api(session, "a/b/c", None)
        
curl_options = "--fail -o /dev/null -s -w '%{http_code} (%{size_download})\\n' -H 'Content-Type: application/octet-stream' -H 'Expect:'"

def put(url, file):
    print(f"PUT {url} -> ", end="", flush=True)
    call("curl -X PUT {} --data @{} {}", url, file, curl_options)

def get(url):
    print(f"GET {url} -> ", end="", flush=True)
    call("curl {} {}", url, curl_options)

def head(url):
    print(f"HEAD {url} -> ", end="", flush=True)
    call("curl --head {} {}", url, curl_options)

def delete(url):
    print(f"DELETE {url} -> ", end="", flush=True)
    call("curl -X DELETE {} {}", url, curl_options)

def receive(url, count):
    return start_process("qreceive --count {} {}", count, url)

class TestServer(object):
    def __init__(self):
        http_port = random_port()
        amqp_port = random_port()
        data_dir = make_temp_dir()

        with working_env(BODEGA_HTTP_PORT_=http_port, BODEGA_DATA_DIR=data_dir):
            self.proc = start_process("bodega")

        self.proc.http_url = f"http://localhost:{http_port}"

    def __enter__(self):
        sleep(0.2);
        return self.proc

    def __exit__(self, exc_type, exc_value, traceback):
        stop_process(self.proc)
