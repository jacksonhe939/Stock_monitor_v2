import yfinance as yf
import json

ticker = yf.Ticker('NVDA')
info = ticker.fast_info

result = {
    'symbol': 'NVDA',
    'price': info.last_price if hasattr(info, 'last_price') else None,
    'previous_close': info.previous_close if hasattr(info, 'previous_close') else None,
}

with open('test_result.json', 'w') as f:
    json.dump(result, f, indent=2, default=str)

print("Done! Check test_result.json")
