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

.NOTPARALLEL:

DESTDIR := ""
PREFIX := ${HOME}/.local
INSTALLED_BODEGA_HOME = ${PREFIX}/share/bodega

export BODEGA_HOME = ${CURDIR}/build
export PATH := ${BODEGA_HOME}/bin:${PATH}
export PYTHONPATH := ${CURDIR}/python:${PYTHONPATH}

BIN_SOURCES := $(shell find bin -type f -name \*.in)
BIN_TARGETS := ${BIN_SOURCES:%.in=build/%}

.PHONY: default
default: build

.PHONY: help
help:
	@echo "build          Build the code"
	@echo "install        Install the code"
	@echo "clean          Clean up the source tree"
	@echo "test           Run the tests"
	@echo "run            Run the server"

.PHONY: clean
clean:
	rm -rf python/__pycache__ python/bodega/__pycache__ scripts/__pycache__
	rm -rf build

.PHONY: build
build: ${BIN_TARGETS} build/prefix.txt
	ln -snf ../python build/python
	ln -snf ../test-data build/test-data

.PHONY: install
install: build
	scripts/install-files build/bin ${DESTDIR}$$(cat build/prefix.txt)/bin
	scripts/install-files python ${DESTDIR}$$(cat build/prefix.txt)/share/bodega/python
	scripts/install-files python/bodega ${DESTDIR}$$(cat build/prefix.txt)/share/bodega/python/bodega
	scripts/install-files test-data ${DESTDIR}$$(cat build/prefix.txt)/share/bodega/test-data

.PHONY: test
test: build
	bodega-test

.PHONY: run
run: build
	bodega

.PHONY: build-image
build-image:
	sudo docker build -t ssorj/bodega .

.PHONY: test-image
test-image:
	sudo docker run --rm --user 9999 -it ssorj/bodega /app/.local/bin/bodega-test

.PHONY: run-image
run-image:
	sudo docker run --rm --user 9999 -p 8080:8080 ssorj/bodega

.PHONY: debug-image
debug-image:
	sudo docker run --rm --user 9999 -p 8080:8080 -it ssorj/bodega /bin/bash

# Prerequisite: docker login

.PHONY: push-image
push-image:
	sudo docker push ssorj/bodega

# To tell the cluster about the new image:
#
# oc tag --source=docker ssorj/bodega:latest bodega:latest

build/prefix.txt:
	echo ${PREFIX} > build/prefix.txt

build/bin/%: bin/%.in
	scripts/configure-file -a bodega_home=${INSTALLED_BODEGA_HOME} $< $@

.PHONY: update-%
update-%:
	curl "https://raw.githubusercontent.com/ssorj/$*/master/python/$*.py" -o python/$*.py
