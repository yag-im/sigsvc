# WebRTC Signalling Service

Based on https://gitlab.freedesktop.org/gstreamer/gst-plugins-rs/-/tree/main/net/webrtc/signalling/src.

Public WebRTC signaling endpoint accessible from both Jukebox clusters and end-users.

## Development

### Prerequisite

Create *.devcontainer/secrets.env* file:

    FLASK_SECRET_KEY=***VALUE***
    FLASK_SECURITY_PASSWORD_SALT=***VALUE***
    AUTH_TOKEN=***VALUE***

The following devcontainers should be up and running:

    sessionsvc

Then simply open this project in any IDE that supports devcontainers (VSCode is recommended).
