site opens at http://localhost:5000 once started

enviorment variables are not in this repository, but are needed to connect to the database. use a local database if credentials are unknown (note: to do so you must set ```drhscit.org``` to ```localhost``` in util.py).

## run w/ docker
download at: https://docs.docker.com/desktop/setup/install/windows-install/

### build, reset, and run containers
```bash
docker-compose up --build
docker exec -it vexnotebooks-ollama-1 ollama pull qwen2.5:7b
docker exec -it vexnotebooks-ollama-1 ollama pull nomic-embed-text
docker-compose exec web python -c "from util import reset; reset()"
docker-compose up -d
```

```docker-compose exec web python [ path ]``` run [ path ] python script

```docker-compose ps``` view status

```docker-compose logs -f [ web / worker / ollama / db ]``` view logs for a container

```docker-compose restart [ web / worker / ollama / db ]``` restart a container

```docker-compose stop``` shuts everything down without deleting data

```docker-compose down``` stops and removes the containers entirely

## run w/o docker
download ollama at: https://ollama.com/download/windows and ensure that it's running

download python at: https://www.python.org/downloads/

### run to install dependencies and get models
```bash 
pip install -r requirements.txt
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

```python -c "from util import reset; reset()"``` reset the database

run both ```python app.py``` and ```python worker.py``` in 2 seperate terminals

note that the pdf data is stored along with the rest of the code. multiple viewers will be unable to see the same pdf data since it's not being put onto a real server.