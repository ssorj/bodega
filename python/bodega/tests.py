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
from fortworth import *

def open_test_session(session):
    enable_logging(level="error")
    session.test_timeout = 10

def test_put_build_python(session):
    test_data_dir = join(session.module.command.home, "test-data")
    build_dir = join(test_data_dir, "build1")
    build_data = BuildData("a", "b", "c")

    with TestServer() as server:
        bodega_put_build(build_dir, build_data, service_url=server.http_url)
        assert bodega_build_exists(build_data, service_url=server.http_url)

def test_put_build_curl(session):
    test_data_dir = join(session.module.command.home, "test-data")
    build_dir = join(test_data_dir, "build1")
    build_data = BuildData("a", "b", "c")

    with TestServer() as server:
        build_url = f"{server.http_url}/{build_data.repo}/{build_data.branch}/{build_data.id}"

        for fs_path in find(build_dir):
            if is_dir(fs_path):
                continue

            relative_path = fs_path[len(build_dir) + 1:]
            request_url = "{0}/{1}".format(build_url, relative_path)

            put(request_url, fs_path)

        get(build_url)

def test_put_build_dry_run(session):
    test_data_dir = join(session.module.command.home, "test-data")
    build_dir = join(test_data_dir, "build1")
    build_data = BuildData("a", "b", None)

    with TestServer() as server:
        bodega_put_build(build_dir, build_data, service_url=server.http_url)
        assert not bodega_build_exists(build_data, service_url=server.http_url)

def test_get(session):
    test_data_dir = join(session.module.command.home, "test-data")
    build_dir = join(test_data_dir, "build1")
    build_data = BuildData("a", "b", "c")

    with TestServer() as server:
        build_url = f"{server.http_url}/{build_data.repo}/{build_data.branch}/{build_data.id}"

        bodega_put_build(build_dir, build_data, service_url=server.http_url)

        get(f"{build_url}/dir1")
        get(f"{build_url}/dir1/")
        get(f"{build_url}/dir1/file4.txt")
        get(f"{build_url}")
        get(f"{build_url}/")
        get(f"{build_url}/file1.txt")
        get(f"{build_url}/file2.zip")
        get(f"{build_url}/file3.bin")
        get(f"{server.http_url}/{build_data.repo}/{build_data.branch}")
        get(f"{server.http_url}/{build_data.repo}/{build_data.branch}/")
        get(f"{server.http_url}/{build_data.repo}")
        get(f"{server.http_url}/{build_data.repo}/")
        get(f"{server.http_url}")
        get(f"{server.http_url}/")

def test_healthz(session):
    with TestServer() as server:
        get(f"{server.http_url}/healthz")

curl_options = "--fail -o /dev/null -s -w '%{http_code} (%{size_download})\\n' -H 'Content-Type: application/octet-stream' -H 'Expect:'"

def put(url, file):
    print(f"PUT {url} -> ", end="", flush=True)
    call("curl -X PUT {} --data-binary @{} {}", url, file, curl_options)

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
        for i in range(10):
            try:
                get(f"{self.proc.http_url}/healthz")
                break
            except CalledProcessError:
                sleep(0.1)
        else:
            raise Exception("Test server timed out")

        return self.proc

    def __exit__(self, exc_type, exc_value, traceback):
        stop_process(self.proc)
