-- BatteryDB: База данных мониторинга батареи
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица устройств (пока пустая, используется позже)
CREATE TABLE devices (
    device_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    device_name VARCHAR(255) DEFAULT 'Новое устройство',
    created_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_devices_user_id ON devices(user_id);

-- Таблица текущих циклов (пока пустая, используется позже)
CREATE TABLE battery_current_cycles (
    device_id UUID PRIMARY KEY REFERENCES devices(device_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    started_at TIMESTAMP,
    last_update TIMESTAMP,
    discharge_start_level INT,
    current_level INT,
    is_charging BOOLEAN,
    state VARCHAR(20)
);

-- Таблица завершённых циклов (пока пустая, используется позже)
CREATE TABLE battery_cycles (
    cycle_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NOT NULL,
    duration_minutes INT NOT NULL,
    health_score FLOAT,
    capacity_degradation FLOAT,
    cycle_count INT NOT NULL,
    charge_cycles_equivalent FLOAT,
    min_level INT,
    max_level INT,
    avg_discharge_rate FLOAT,
    avg_charge_rate FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cycles_user_id ON battery_cycles(user_id);
CREATE INDEX idx_cycles_device_id ON battery_cycles(device_id);
CREATE INDEX idx_cycles_completed_at ON battery_cycles(completed_at DESC);

COMMENT ON TABLE devices IS 'Устройства пользователей';
COMMENT ON TABLE battery_cycles IS 'Завершённые циклы для аналитики';