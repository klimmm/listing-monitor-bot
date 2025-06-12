#!/bin/bash

# Script to run the parser locally
# This replaces the old GitHub Actions workflow trigger

echo "Starting Cian parser..."
python3 parser.py

echo "Parser execution completed!"