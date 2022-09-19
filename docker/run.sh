#!/usr/bin/env bash

BASE=$(dirname $0)

cd $BASE
docker-compose up -d --build --remove-orphans
