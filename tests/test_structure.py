import sys
import os
import json
from structure_service import get_chart_data

data = get_chart_data('EURUSD', '1d', 'forex')

if 'payload' in data:
    print("Candles found:", len(data['payload']['candles']))
    print(data['payload']['candles'][0])
else:
    print("Error:", data)
