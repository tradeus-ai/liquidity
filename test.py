from src.web_dashboard import render_dashboard
from unittest.mock import patch

payload = {
    'candles': [{'time': 1600000000, 'open': 100, 'high': 110, 'low': 90, 'close': 105}],
    'inside_zones': [],
    'htf_events': [],
    'htf_zones': [],
    'fvgs': []
}

@patch('src.web_dashboard.get_chart_data', return_value=payload)
def test_all_on(mock):
    html = render_dashboard('TEST', '1d', 'futures', show_fvg=True, show_structure=True, show_zones=True)
    assert 'features.forEach(f => {' in html
    assert 'lwHandler.legend ? lwHandler.legend.seriesContainer : null' in html
    assert 'span style="color: ${f.color}' in html
    print('Test 1 (JS Inject present): PASSED')

test_all_on()
