git pull origin full_new
docker compose down fastapi
docker compose up -d fastapi
docker compose logs -f fastapi