import os
import json
import time
import concurrent.futures
from symbol_loader import get_symbol_list
from structure_service import get_chart_data

CACHE_FILE = "data/screener_cache.json"

def process_symbol(sym):
    try:
        data = get_chart_data(sym, '1d')
        if 'error' in data:
            return None
            
        current_state = data.get('current_state')
        if not current_state:
            return None
            
        return {
            'symbol': sym,
            'trend': current_state.get('trend'),
            'inducement_done': current_state.get('inducement_done')
        }
    except Exception as e:
        print(f"Error processing {sym}: {e}")
        return None

def get_screener_data(force_refresh=False):
    import datetime
    
    # Check cache first
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
                
            # Check if cache is from today
            cache_ts = cached_data.get('timestamp', 0)
            cache_date = datetime.datetime.fromtimestamp(cache_ts).date()
            today_date = datetime.date.today()
            
            if cache_date == today_date:
                cached_data['cached'] = True
                return cached_data
            else:
                print(f"Cache is from {cache_date}, but today is {today_date}. Forcing refresh.")
        except Exception as e:
            print(f"Error reading screener cache: {e}")

    symbols = get_symbol_list()
    results = []
    
    # Use ThreadPool to scan symbols concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(process_symbol, sym): sym for sym in symbols}
        
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                results.append(res)
                    
    # Sort alphabetically
    results.sort(key=lambda x: x['symbol'])
    
    payload = {
        'data': results,
        'cached': False,
        'timestamp': int(time.time())
    }

    # Write to cache
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(payload, f)
    except Exception as e:
        print(f"Error writing screener cache: {e}")

    return payload


if __name__ == "__main__":
    import time
    start = time.time()
    print("Fetching screener data...")
    res = get_screener_data()
    print(f"Done in {time.time() - start:.2f}s")
    for k, v in res.items():
        print(f"{k}: {len(v)} symbols")
