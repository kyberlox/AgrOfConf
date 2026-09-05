#!/bin/sh
git pull origin main

docker-compose stop frontend
docker-compose rm frontend
docker-compose up -d --build frontend 