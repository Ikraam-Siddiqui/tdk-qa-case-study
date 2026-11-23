# TDK QA Engineer Case Study – LibreChat v0.8.7

This repository contains the performance test scripts, local mock AI server, test configurations, raw Locust reports, and the final QA Case Study Report for LibreChat v0.8.7.

## Repository Structure
- `report/` – Final QA Case Study Report (PDF)
- `performance/` – Locust test script (`locustfile.py`), Mock AI server (`mock_openai.py`), and HTML/CSV reports for Baseline, Load (25 users), and Stress (100 users) runs
- `config/` – `librechat.yaml` and `docker-compose.override.yml` used during testing

## How to Run the Performance Tests
1. Start LibreChat v0.8.7 locally (`http://localhost:3080`) with MongoDB and Meilisearch running in Docker.
2. Start the local Mock AI server:
   ```bash
   uvicorn performance.mock_openai:app --host 0.0.0.0 --port 8000
```
(Or run python performance/mock_openai.py if it uses uvicorn.run directly.)
3. Install Locust and start the test suite:
pip install locust
locust -f performance/locustfile.py --host=http://localhost:3080
4. Open http://localhost:8089 in your browser and run the Baseline (5 users), Load (25 users), and Stress (100 users) tests.