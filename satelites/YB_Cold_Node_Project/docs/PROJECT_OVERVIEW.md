
# YB Cold Node — Project Overview

## Purpose
YB Cold Node is a hardware + software subsystem of YeastBank designed to monitor and control refrigeration equipment used to store yeast cultures.

It provides:

- Local temperature control
- Sensor monitoring
- Alert generation
- Data logging
- Integration with the YeastBank API
- Association between storage equipment and biological inventory

## Key Capabilities

- Temperature control with setpoint and hysteresis
- Local display + buttons interface
- Wi‑Fi connectivity
- Offline buffering of telemetry
- Alert system
- Integration with YeastBank backend

## Core Philosophy

The system must:

1. Continue operating even without internet
2. Provide reliable temperature control
3. Maintain historical traceability
4. Integrate seamlessly with YeastBank inventory

## Architecture Layers

Hardware Layer
ESP32, sensors, relays, display.

Firmware Layer
Control logic, connectivity, configuration.

Platform Layer
YeastBank API, dashboards, alerts and telemetry storage.
