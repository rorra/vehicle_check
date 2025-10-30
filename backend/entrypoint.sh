#!/bin/bash
set -e

echo "Waiting for database to be ready..."
sleep 10

echo "Running database migrations..."
alembic upgrade head

echo "Creating test data..."
python script/create_test_data.py

# echo "Creating availability slots..."
# python script/populate_availability_slots.py || true

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
