#!/usr/bin/env bash

# set defaults
export LISTEN_IP="${LISTEN_IP:-0.0.0.0}"
export LISTEN_PORT="${LISTEN_PORT:-80}"

exec python -m sigsvc.main
