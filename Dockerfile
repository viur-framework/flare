FROM python:3.9.5-alpine3.13

ENV PROJECT_WORKSPACE=/workspace

RUN apk add --no-cache bash

#install python requirements
COPY requirements.txt /
RUN pip3 install -r requirements.txt

COPY tools /tools


#expose
VOLUME ["/workspace"]

ENTRYPOINT /bin/bash
