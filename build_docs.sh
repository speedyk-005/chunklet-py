#!/bin/bash

# Build the Python package
uv build

# Set PYTHONPATH to include the src directory for mkdocstrings
export PYTHONPATH=$(pwd)/src:$PYTHONPATH

# Build the MkDocs documentation
uv python -m mkdocs build

# Deploy the documentation using mike
uv run mike deploy --push --update-aliases 2.4.2 latest
