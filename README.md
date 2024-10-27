# WebRTC Signalling Service

Based on https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc/signalling/src.

Public signaling endpoint accessible from both Jukebox clusters and users.

## Run locally

python app.py

or use vscode debugger

## Publish new version

1. From devcontainer build app package:

        make build

2. From outside of devcontainer build and pub a docker image:

        make docker-pub TAG=0.0.15
