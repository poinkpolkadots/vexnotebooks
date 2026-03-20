download ollama at: https://ollama.com/download/windows

## run w/ docker
download at: https://docs.docker.com/desktop/setup/install/windows-install/
use local testing w/ docker env variables

### build, reset, and run containers
```bash
bash docker-compose down #only if is currently running
docker-compose up --build
docker exec -it vexnotebooks-ollama-1 ollama pull qwen2.5:7b
docker exec -it vexnotebooks-ollama-1 ollama pull llama3.2:3b
docker exec -it vexnotebooks-ollama-1 ollama pull nomic-embed-text
docker-compose exec web python -c "from util import reset; reset()"
docker-compose up -d
```
site opens at http://localhost:5000

```bash docker-compose exec web python [ path ]``` run [ path ] python script

```bash docker-compose ps``` view status

```bash docker-compose logs -f [ web / worker / ollama / db ]``` view logs for a container
```bash docker-compose restart [ web / worker / ollama / db ]``` restart a container

```bash docker-compose stop``` shuts everything down without deleting data

```bash docker-compose down``` stops and removes the containers entirely

## run w/o docker
ensure that ollama is currently running

```bash pip install -r requirements.txt``` run to install dependencies