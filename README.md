Once the site is started by running app.py, you can access it at http://localhost:5000

Environment variables are not in this repository, but are needed to connect to the database. Use a local database if credentials are unknown (note: to do so you must set ```drhscit.org``` to ```localhost``` in util.py where ```DB_HOST = 'db' if IN_DOCKER else 'drhscit.org'```).
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

## Code Structure and Project Completion For Future Teams
### Completed Requirements
- Completely implemented Flask
  - Got all routes completed
  - Got uploading files to work
  - Got HTML templates to work
  - Got LLM and HTML connected
- Styling and layout (HTML + CSS) are finished
- Completed predetermined prompts for AI

### File Structure
| File | Description |
-------|--------------
| base.html | Provides base template for the catalog, home, notebookinfo, and upload |
| catalog.html | List of all the notebooks |
| home.html | Serves as the homepage for the upload and catalog page |
| notebookinfo.html | Contain the responses and predetermined prompts |
| upload.html | Uploading the PDF files into the database |
| app.py | Runs the site itself, managing all of the html templates |
| worker.py | Iterates through the table, creating indexes for PDFs that need them or generating responses |
| util.py | Contains utility functions for accessing the database and running processes with the LLM |
| prompts.yaml | Tells the model what to do to files and how to analyze them |
| requirements.txt | A list of python dependencies that the code needs to run |
#### Dockerfile and docker-compose.yml manage the initialization of the Docker containers; there are 4 that the app runs on (the LLM runs *extremely* slow on Docker, further optimization will need to be done)

### Find default .env file in Code Documentation For Future Teams in Google Drive

### Unfinished Requirements
- Functionality of filtering entries and sorting catalog page
- Functionality of separate completeness score
- Section presence checklist in UI
- Flagging entries for judges to review
- Stretch goals
  - Similarity detection (compare multiple notebooks to spot copy/paste issues)
  - Writing-style consistency flag
  - Export to CSV or Google Sheets
- Actual separation of notebook information sections into divisions in HTML (currently just displays with markdown headings)
- General optimization of the application, and eventual migration to client hosting
