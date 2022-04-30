# Docker files for scio

## Requirements

You will need docker and docker-compose to run scio in docker.

## Create network for SCIO containers

```bash
sudo docker network create scio
```

## Run

Run analyze, tika-server and api:

```bash
docker-compose up --build --remove-orphans
```

###
Remove all data from docker instance

```bash
docker-compose down --volumes
```
