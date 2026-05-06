from datetime import datetime

from app.services.battery_math import avg_load_mw, integrate_discharge


def test_integrate_discharge_preserves_subsecond_intervals():
    previous = datetime.fromisoformat("2026-05-05T20:48:44.285")
    current = datetime.fromisoformat("2026-05-05T20:48:45.150")

    energy_mwh, duration_seconds = integrate_discharge(previous, 10000, current)

    assert duration_seconds == 0.865
    assert round(energy_mwh, 4) == round(10000 * (0.865 / 3600), 4)


def test_avg_load_uses_fractional_duration_seconds():
    load = avg_load_mw(12.5, 0.75)

    assert round(load or 0.0, 4) == 60000.0
