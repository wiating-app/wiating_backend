FROM debian:latest

RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && apt-get install -y curl git python3-pip python-setuptools python3-dev

RUN mkdir -p /opt/wiating/devops
RUN mkdir -p /images

COPY requirements.txt .
COPY requirements_test.txt .

RUN pip3 install -r requirements_test.txt

WORKDIR /opt/wiating
RUN chmod -R g+rwx ./
