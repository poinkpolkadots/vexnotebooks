Once the site is started by running app.py, you can access it at http://localhost:5000

Environment variables are not in this repository, but are needed to connect to the database. Use a local database if credentials are unknown (note: to do so you must set ```DB_HOST = drhscit.org``` to ```DB_HOST = localhost``` in util.py).
If using Docker, the Docker PostgreSQL database will automatically be used, but DB, DB_UN, and DB_PW env vars must still be set.

## Run with Docker
Must have Docker downloaded. You can download it [here](https://docs.docker.com/desktop/setup/install/windows-install/).

### Code to build and run containers
```bash
docker compose up --build -d
docker exec -it vexnotebooks-ollama-1 ollama pull qwen2.5:7b
docker exec -it vexnotebooks-ollama-1 ollama pull nomic-embed-text
docker-compose exec web python -c "from util import reset; reset()"
```

```docker-compose ps``` view status

```docker-compose logs -f [ web / worker / ollama / db ]``` view logs for a container

```docker-compose down``` stops and removes the containers entirely

## Run without Docker
You must download Ollama first. You can download it [here](https://ollama.com/download), then ensure that it's running.

You must have Python installed. You can download it [here](https://www.python.org/downloads/).

### Install Python libraries and required models
```bash
pip install -r requirements.txt
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

```python -c "from util import reset; reset()"``` reset the database.

Run both ```python app.py``` and ```python worker.py``` at the same time. Ensure they are both running.

*Note that the PDF data is stored along with the rest of the code. Multiple viewers will be unable to see the same PDF data since it's not being put onto a real server.*
