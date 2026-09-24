#!/bin/bash
# User data para solventa-loadgen (Ubuntu 24.04): k6 + cliente psql + git + tmux.
set -eux
apt-get update -y
apt-get install -y git postgresql-client tmux curl python3
K6_VERSION=$(curl -s https://api.github.com/repos/grafana/k6/releases/latest | grep -Po '"tag_name": "\K[^"]+')
curl -sL "https://github.com/grafana/k6/releases/download/${K6_VERSION}/k6-${K6_VERSION}-linux-amd64.tar.gz" | tar xz -C /tmp
cp /tmp/k6-*/k6 /usr/local/bin/k6
k6 version > /home/ubuntu/user-data-ok
