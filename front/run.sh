#!/bin/bash

if [ "$ENVIRONMENT" == "dev" ]; then
  uvicorn front.main:app --host 0.0.0.0 --port 8000 --reload
else
  uvicorn front.main:app --host 0.0.0.0 --port 8000
fi
