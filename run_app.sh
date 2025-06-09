#!/bin/bash

# Script to run the Flask accounting application

echo "Starting the Accounting App..."
export FLASK_APP=src/main.py
flask run --host=0.0.0.0 --port=8080
echo "Application stopped."