#!/bin/bash
pytest tests/
python3 scripts/validate_json.py tests/http/expected_responses/sensor_response.json sensor
