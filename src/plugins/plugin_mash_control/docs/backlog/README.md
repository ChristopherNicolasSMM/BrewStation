# Mash Control Backlog & Process

This folder contains tracking information for the plugin's development.
It is used by humans and by AI agents that may continue work later.

## Current state

- **Phase 6 (Recipes)** implemented on 2026‑03‑12. Model, service, API,
  frontend, and route completed.
- Plants system (Phase 5) already stable and in production.
- Debug instrumentation removed from JS.

## Next steps

1. **Phase 7 – Mash Schedule**
   * Generate step schedules from a recipe
   * Allow reordering / editing schedule
   * Integrate with session control
2. **Phase 8 – Brew Session / Batch**
   * Execute recipe/schedule with instruments
   * Persist runtime telemetry
   * Support manual/semi/automatic modes
3. **Phase 9 – Hardware Integration**
   * Device manager mapping roles to physical devices
   * Control actuators and read sensors
4. **Phase 10 – Analytics & Sharing**
   * Graphs, exporting, sharing with cloud services

Refer to `backlog_tech.md` for architectural notes.

## How to use

When taking over development, start with the next uncompleted phase and
read through the existing code (models, service, API, UI). The previous
phases follow a pattern: for each domain object you create

* SQLAlchemy model in `mash_models.py`
* Service class with CRUD in `services/`
* API endpoints in `api/routes/mash_routes.py`
* HTML template and JS manager in `static/js/`
* Register model in `plugin.py` and helper in `model_loader.py`
* Add web route in `controller/routes.py`

Keep naming conventions consistent (English plus Portuguese labels).
Consult earlier sections of this document for details.