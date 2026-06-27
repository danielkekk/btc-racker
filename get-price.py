import urllib.request
import json
import os
from datetime import datetime

APIS = [
    {
        "name": "Binance",
        "url": "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT",
        "parse": lambda d: (float(d["lastPrice"]), float(d["priceChangePercent"])),
    },
    {
        "name": "CoinGecko",
        "url": "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true",
        "parse": lambda d: (d["bitcoin"]["usd"], d["bitcoin"]["usd_24h_change"]),
    },
    {
        "name": "Kraken",
        "url": "https://api.kraken.com/0/public/Ticker?pair=XBTUSD",
        "parse": lambda d: (float(d["result"]["XXBTZUSD"]["c"][0]), None),
    },
]

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")
ALERT_THRESHOLD = 65_000  # USD

def send_push(title, message, priority="high"):
    if not NTFY_TOPIC:
        print("NTFY_TOPIC nincs beállítva, push értesítés kihagyva.")
        return
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": priority,
                "Tags": "bitcoin,warning",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
        print(f"Push értesítés elküldve → ntfy.sh/{NTFY_TOPIC}")
    except Exception as e:
        print(f"Push értesítés sikertelen: {e}")

def get_btc_price():
    for api in APIS:
        try:
            req = urllib.request.Request(api["url"], headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            price, change_24h = api["parse"](data)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if change_24h is not None:
                direction = "▲" if change_24h >= 0 else "▼"
                change_str = f"{direction} {change_24h:+.2f}% (24h)"
            else:
                change_str = ""

            print(f"[{timestamp}] BTC/USD: ${price:,.2f}  {change_str}  (forrás: {api['name']})")

            if price < ALERT_THRESHOLD:
                print(f"FIGYELEM: Az ár ${price:,.2f} — ez ${ALERT_THRESHOLD:,} alatt van! Push küldése...")
                send_push(
                    title=f"BTC riasztás: ${price:,.2f}",
                    message=f"A Bitcoin ára ${ALERT_THRESHOLD:,} alá esett!\n{change_str}\n{timestamp}\nForrás: {api['name']}",
                )
            else:
                print(f"Az ár ${price:,.2f} — a ${ALERT_THRESHOLD:,} küszöb felett van, push nem szükséges.")

            return price

        except Exception as e:
            print(f"[{api['name']}] nem elérhető: {e}")

    print("Egyik API sem elérhető.")
    return None

if __name__ == "__main__":
    get_btc_price()
