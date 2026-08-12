import requests

r = requests.get("http://127.0.0.1:8080/chart_data?symbol=ABB&timeframe=1d")
data = r.json()
print("Total zones returned:", len(data.get('htf_zones', [])))
for z in data.get('htf_zones', []):
    print(z['type'], z['start_time'], z['end_time'], z['status'])
