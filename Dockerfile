FROM buildpack-deps:buster

#default workdirs
#bitbucket WORKDIR /opt/atlassian/bitbucketci/agent/build
#google    WORKDIR /workspace
#github    WORKDIR ${GITHUB_WORKSPACE} < use (/home/runner/work/myrepo/myrepo)
#local     WORKDIR /workspace

#all scripts use this variable
ENV PROJECT_WORKSPACE=/workspace

#install python3.8
RUN wget https://pascalroeleven.nl/deb-pascalroeleven.gpg && apt-key add deb-pascalroeleven.gpg
RUN echo "deb http://deb.pascalroeleven.nl/python3.8 buster-backports main" >> /etc/apt/sources.list

#install system requirements
RUN apt-get update && apt-get install -y zip python3-pip python3.8

# activate 3.8 as default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1

#get udated nodejs
RUN curl -sL https://deb.nodesource.com/setup_15.x  | bash -
RUN apt-get -y install nodejs

#install python requirements
COPY requirements.txt /
RUN pip3 install -r requirements.txt


COPY scripts /scripts

#expose
VOLUME ["/workspace"]

ENTRYPOINT /bin/bash


#fetch pyodide 0.16.1 put pyodide in deploy folder
#RUN python3 /scripts/get-pyodide.py -t ${PROJECT_WORKSPACE}/deploy/pyodide

#build less files with gulp
#RUN python3 /scripts/gulp.py -t css

#deliver project to target
#RUN python3 /scripts/flare.py -t ${PROJECT_WORKSPACE}/deploy/vi -s ${PROJECT_WORKSPACE}/sources/vi_app -m 1 -c 1 -z 1