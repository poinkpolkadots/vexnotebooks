FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]

# HELP
# docker-compose up --build -d
# docker exec -it vexnotebooks-ollama-1 ollama pull qwen2.5:7b
# docker exec -it vexnotebooks-ollama-1 ollama pull llama3.2:3b
# docker exec -it vexnotebooks-ollama-1 ollama pull nomic-embed-text

# docker-compose up -d (run container)
# docker-compose exec web python [ path ] (run python script)
# docker-compose exec web python -c "from util import reset; reset()" (reset db)

# opens at http://localhost:5000

# docker-compose ps (containers are running or crashed)
# docker-compose logs -f [ web / worker / ollama ] ("print" statements and errors)
# docker-compose stop (shuts everything down without deleting data)
# docker-compose down (stops and removes the containers entirely)
