#!/bin/bash
set -e

echo "Starting E2E Test Suite..."
# Spin up the specialized test composition
docker-compose -f docker-compose.test.yml up -d --build

echo "Waiting for services to be ready..."
sleep 15

echo "Running E2E verification specs..."
# In a real scenario, this command would run a Playwright/Cypress or Python requests test-suite container
docker-compose -f docker-compose.test.yml run e2e_runner

echo "Tests complete! Tearing down..."
docker-compose -f docker-compose.test.yml down -v
