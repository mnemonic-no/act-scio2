# Docker files for scio

Run analyze, tika-server and api:

```bash
sudo docker network create scio
cd docker
./run.sh
```

### 
Remove all data from docker instance

```bash
docker-compose down --volumes
```

### Example queries that should have hits on sample data:

```
docker exec -it docker-app-1 /bin/bash
http_proxy= poetry run script/populate_sample_queries.sh $METASEARCH_APIKEY
```
