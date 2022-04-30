# Docker files for scio

## Requirements

You will need docker and docker-compose to run scio in docker.

# NLTK data

Download nltk data locally so they are available under ~/nltk-data (e.g. by using scio-nltk-download).


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
