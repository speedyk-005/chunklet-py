#!/bin/bash

# Build the Python package
python -m build

# Set PYTHONPATH to include the src directory for mkdocstrings
export PYTHONPATH=$(pwd)/src:$PYTHONPATH

# Build the MkDocs documentation
python -m mkdocs build

# Deploy the documentation using mike
# mike deploy --push --update-aliases 2.2.0 latest
