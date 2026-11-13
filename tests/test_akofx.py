"""AKO FX P-Gap detector and chart integration tests."""
from modules import chart_overlays, indicator_profiles, technical
from modules.execution import run_module

def bullish_gap():
    return [
        {'time': 100, 'open': 99.0, 'high': 100.0, 'low': 98.0, 'close': 99.5},
        {'time': 160, 'open': 100.0, 'high': 108.0, 'low': 99.5, 'close': 105.0},
        {'time': 220, 'open': 107.0, 'high': 108.0, 'low': 106.0, 'close': 107.5},
    ]

def bearish_gap():
    return [
        {'time': 100, 'open': 107.0, 'high': 108.0, 'low': 106.0, 'close': 107.5},
        {'time': 160, 'open': 105.0, 'high': 105.5, 'low': 97.0, 'close': 100.0},
        {'time': 220, 'open': 99.0, 'high': 99.5, 'low': 98.0, 'close': 98.5},
    ]

def test_akofx_detects_bullish_p_gap():
    result = run_module('akofx', {'candles': bullish_gap(), 'now': 221, 'symbol': 'EURUSD'})
    assert result['status'] == 'ok'
    assert result['event_count'] == 1
    event = result['events'][0]
    assert event['event_type'] == 'p-gap'
    assert event['direction'] == 'bullish'
    assert (event['gap_low'], event['gap_high']) == (100.0, 106.0)
    assert event['middle_body'] == 5.0
    assert event['middle_total_shadow'] == 3.5
    assert event['status'] == 'confirmed'

def test_akofx_detects_bearish_p_gap():
    result = technical.run('akofx', {'candles': bearish_gap(), 'now': 221})
    assert result['event_count'] == 1
    assert result['events'][0]['direction'] == 'bearish'
    assert (result['events'][0]['gap_low'], result['events'][0]['gap_high']) == (99.5, 106.0)

def test_akofx_rejects_equal_body_and_total_shadow():
    rows = bullish_gap()
    rows[1] = {'time': 160, 'open': 100.0, 'high': 107.0, 'low': 98.0, 'close': 105.0}
    result = technical.run('akofx', {'candles': rows, 'now': 221})
    assert result['events'] == []

def test_akofx_rejects_overlapping_first_and_third_candles():
    rows = bullish_gap()
    rows[2] = {'time': 220, 'open': 99.0, 'high': 101.0, 'low': 99.0, 'close': 100.0}
    result = technical.run('akofx', {'candles': rows, 'now': 221})
    assert result['events'] == []

def test_akofx_marks_open_third_candle_provisional():
    rows = bullish_gap()
    rows[2]['is_open'] = True
    result = technical.run('akofx', {'candles': rows, 'now': 221})
    assert result['events'][0]['status'] == 'provisional'

def test_akofx_chart_overlay_receives_chart_candles():
    profile = {'id': 'akofx-profile', 'name': 'AKO FX', 'type': 'akofx', 'parameters': {}, 'enabled': True}
    result = chart_overlays.calculate('alice', [profile], {'candles': bullish_gap(), 'symbol': 'EURUSD'}, end_time=221)
    assert result[0]['result']['status'] == 'ok'
    assert result[0]['result']['event_count'] == 1

def test_akofx_indicator_profiles_are_owner_scoped(tmp_path, monkeypatch):
    monkeypatch.setenv('DASHBOARD_MODULE_STATE_DIR', str(tmp_path))
    saved = indicator_profiles.save('alice', {'name': 'AKO FX P-Gap', 'type': 'akofx', 'parameters': {}, 'enabled': True})
    assert saved['type'] == 'akofx'
    assert any(item['id'] == saved['id'] for item in indicator_profiles.list_profiles('alice'))
    assert not any(item['id'] == saved['id'] for item in indicator_profiles.list_profiles('bob'))

def test_akofx_settings_reject_unknown_fields_and_invalid_colors():
    import pytest
    with pytest.raises(ValueError):
        technical.settings('akofx', {'minimum_body_percent': 60})
    with pytest.raises(ValueError):
        technical.settings('akofx', {'bullish_color': 'green'})
