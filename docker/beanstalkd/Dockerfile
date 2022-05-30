FROM docker.io/debian:buster

RUN apt update
RUN apt -y install beanstalkd

ENTRYPOINT ["/usr/bin/beanstalkd"]
