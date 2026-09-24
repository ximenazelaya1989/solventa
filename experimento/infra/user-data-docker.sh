#!/bin/bash
# User data para solventa-app y solventa-db (Ubuntu 24.04).
# Se pega en EC2 > Launch instance > Advanced details > User data.
set -eux
apt-get update -y
apt-get install -y docker.io docker-compose-v2 git postgresql-client
systemctl enable --now docker
usermod -aG docker ubuntu
echo "listo" > /home/ubuntu/user-data-ok
