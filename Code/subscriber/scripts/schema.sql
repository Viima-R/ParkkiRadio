-- =============================================================================
-- TPMS Database Schema
-- Database: parkkiradio
-- =============================================================================

-- ---------------------------------------------------------------------------
-- idapp_location
-- One row per physical reader location (Raspberry Pi unit).
-- Populated at install time with the location's ID and description.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS idapp_location (
    location_id     VARCHAR(32)     PRIMARY KEY,
    description     TEXT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- ---------------------------------------------------------------------------
-- idapp_carid
-- Known/authorized cars. Each row maps one TPMS sensor ID to a car.
-- A car with 4 sensors will have 4 rows, all sharing the same car_label.
-- Some rows are pre-registered; others are promoted from idapp_timer
-- by an operator once a car is identified.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS idapp_carid (
    tpms_id         VARCHAR(32)     PRIMARY KEY,
    car_label       VARCHAR(64)     NOT NULL,       -- e.g. licence plate or owner name
    location_id     VARCHAR(32)     REFERENCES idapp_location(location_id),
    registered_at   TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    notes           TEXT
);

-- ---------------------------------------------------------------------------
-- idapp_timer
-- Active car sightings. One row per car_label currently detected.
-- first_seen: when this parking session started
-- last_seen:  updated every time a sensor from this car is received
-- overtime:   flag set by a separate process (Django/cron) when limit exceeded
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS idapp_timer (
    car_label       VARCHAR(64)     PRIMARY KEY,
    location_id     VARCHAR(32)     NOT NULL REFERENCES idapp_location(location_id),
    first_seen      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    last_seen       TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    is_known        BOOLEAN         NOT NULL DEFAULT FALSE,
    overtime        BOOLEAN         NOT NULL DEFAULT FALSE
);

-- Index for quick location-based queries
CREATE INDEX IF NOT EXISTS idx_timer_location ON idapp_timer(location_id);
CREATE INDEX IF NOT EXISTS idx_carid_car_label ON idapp_carid(car_label);
