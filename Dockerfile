FROM buildpack-deps:bullseye

#default workdirs
#bitbucket WORKDIR /opt/atlassian/bitbucketci/agent/build
#google    WORKDIR /workspace
#github    WORKDIR ${GITHUB_WORKSPACE} < use (/home/runner/work/myrepo/myrepo)
#local     WORKDIR /workspace

#all scripts use this variable
ENV PROJECT_WORKSPACE=/workspace

#install system requirements and python
RUN apt-get update && apt-get install -y zip python3-pip python3 rsync

#get udated nodejs
RUN curl -sL https://deb.nodesource.com/setup_15.x  | bash -
RUN apt-get -y install nodejs

#install python requirements
COPY requirements.txt /
RUN pip3 install -r requirements.txt


COPY tools /tools

#expose
VOLUME ["/workspace"]

ENTRYPOINT /bin/bash
