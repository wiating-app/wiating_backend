FROM debian:bookworm

RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && apt-get install -y curl git python3-pip python3-setuptools python3-dev zlib1g-dev libjpeg-dev

RUN mkdir -p /opt/wiating/devops
RUN mkdir -p /images

COPY requirements.txt .
COPY requirements_test.txt .

RUN pip3 install --break-system-packages -r requirements.txt
RUN pip3 install --break-system-packages -r requirements_test.txt

WORKDIR /opt/wiating

RUN mkdir -p /opt/wiating/wiating_backend

COPY wiating_backend /opt/wiating/wiating_backend

RUN chmod -R g+rwx ./
