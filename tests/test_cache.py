import datetime
import time

ts = time.time()
print("Timestamp:", ts)

cache_date = datetime.datetime.fromtimestamp(ts).date()
today = datetime.date.today()

print("Cache Date:", cache_date)
print("Today:", today)
print("Is same day?", cache_date == today)
