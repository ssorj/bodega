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

FROM registry.fedoraproject.org/fedora-minimal

RUN microdnf --nodocs install make gcc python3-devel python3-requests && microdnf clean all

COPY . /app/src
ENV HOME=/app
WORKDIR /app/src

RUN pip3 install --user starlette uvicorn aiofiles
RUN make clean install

RUN chown -R 1001:0 /app && chmod -R 775 /app
USER 1001

EXPOSE 8080

ENV PATH=/app/.local/bin:$PATH
CMD ["bodega"]
