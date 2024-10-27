#!/usr/bin/env bash

mkdir -p /workspaces/sigsvc/.vscode
cp /workspaces/sigsvc/.devcontainer/vscode/* /workspaces/sigsvc/.vscode

make bootstrap
