#!/bin/sh
git pull origin full_new

docker-compose stop frontend
docker-compose rm frontend
docker-compose up -d --build frontend 