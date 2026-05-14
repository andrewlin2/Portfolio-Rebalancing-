import json
import threading
import webview

# Import the core functions from the CLI module
from Rebalancer import (
    set_portfolio,
    get_current_prices,
    check_rebalance,
    execute_rebalance,
    execute_transaction,
    set_portfolio_weight_change,
    get_rebalance_recommendations,
)


class Api:
    def __init__(self):
        self.threshold = 5.0

    def set_portfolio(self, holdings_json: str):
        """Accept JSON mapping ticker -> [quantity, target_weight] or {ticker: [q,w]}"""
        try:
            data = json.loads(holdings_json)
            # normalize to expected dict format
            holdings = {}
            for k, v in data.items():
                if isinstance(v, (list, tuple)) and len(v) >= 2:
                    qty = float(v[0])
                    wt = float(v[1])
                elif isinstance(v, dict) and "quantity" in v and "weight" in v:
                    qty = float(v["quantity"]) 
                    wt = float(v["weight"]) 
                else:
                    return {"error": f"invalid value for {k}, expected [quantity, weight]"}
                holdings[k.upper()] = (qty, wt)

            res = set_portfolio(holdings)
            return {"ok": True, "portfolio": holdings}
        except Exception as e:
            return {"error": str(e)}

    def get_prices(self, tickers_csv: str):
        try:
            tickers = [t.strip().upper() for t in tickers_csv.split(",") if t.strip()]
            prices = get_current_prices(tickers)
            return {"prices": prices}
        except Exception as e:
            return {"error": str(e)}

    def check_rebalance(self, threshold: float = None):
        try:
            thr = self.threshold if threshold is None else float(threshold)
            return check_rebalance(threshold=thr)
        except Exception as e:
            return {"error": str(e)}

    def execute_rebalance(self):
        try:
            txns = execute_rebalance(record=True)
            return {"transactions": txns}
        except Exception as e:
            return {"error": str(e)}

    def execute_transaction(self, ticker: str, action: str, shares: float, price: float = None):
        try:
            tx = execute_transaction(ticker=ticker, action=action, shares=float(shares), price=(float(price) if price else None), record=True)
            return {"transaction": tx}
        except Exception as e:
            return {"error": str(e)}

    def set_weights(self, weights_json: str):
        try:
            data = json.loads(weights_json)
            set_portfolio_weight_change(data)
            return {"ok": True}
        except Exception as e:
            return {"error": str(e)}

    def set_threshold(self, thr: float):
        try:
            t = float(thr)
            if not (0 <= t < 100):
                return {"error": "threshold must be >=0 and <100"}
            self.threshold = t
            return {"ok": True, "threshold": self.threshold}
        except Exception as e:
            return {"error": str(e)}


HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Portfolio Rebalancer</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 20px; }
      textarea { width: 100%; height: 80px; }
      pre { background: #f4f4f4; padding: 10px; max-height: 300px; overflow: auto; }
      .block { margin-bottom: 16px; }
    </style>
  </head>
  <body>
    <h2>Portfolio Rebalancer (GUI)</h2>

    <div class="block">
      <h3>Set portfolio</h3>
      <p>Provide JSON mapping, e.g. {"SPY": [100, 0.3], "TLT": [50, 0.7]}</p>
      <textarea id="holdings">{"SPY": [100, 0.3], "TLT": [50, 0.7]}</textarea>
      <button onclick="setPortfolio()">Set portfolio</button>
    </div>

    <div class="block">
      <h3>Get prices</h3>
      <input id="tickers" value="SPY,TLT,GLD" style="width:60%"/>
      <button onclick="getPrices()">Get prices</button>
    </div>

    <div class="block">
      <h3>Check rebalance</h3>
      <input id="threshold" placeholder="threshold % (optional)" style="width:120px"/>
      <button onclick="checkRebalance()">Check</button>
      <button onclick="executeRebalance()">Execute Rebalance</button>
    </div>

    <div class="block">
      <h3>Arbitrary transaction</h3>
      <input id="tx_ticker" placeholder="TICKER" style="width:120px"/>
      <input id="tx_action" placeholder="buy/sell" style="width:120px"/>
      <input id="tx_shares" placeholder="shares" style="width:120px"/>
      <input id="tx_price" placeholder="price (optional)" style="width:120px"/>
      <button onclick="doTransaction()">Record Transaction</button>
    </div>

    <div class="block">
      <h3>Set weights</h3>
      <p>Provide JSON mapping ticker->weight for all portfolio tickers, e.g. {"SPY":0.4,"TLT":0.6}</p>
      <textarea id="weights">{"SPY":0.4,"TLT":0.6}</textarea>
      <button onclick="setWeights()">Set weights</button>
    </div>

    <h3>Output</h3>
    <pre id="output">ready</pre>

    <script>
      function show(obj){ document.getElementById('output').textContent = JSON.stringify(obj,null,2); }
      async function setPortfolio(){ const v=document.getElementById('holdings').value; show(await window.pywebview.api.set_portfolio(v)); }
      async function getPrices(){ const v=document.getElementById('tickers').value; show(await window.pywebview.api.get_prices(v)); }
      async function checkRebalance(){ const v=document.getElementById('threshold').value; const res=await window.pywebview.api.check_rebalance(v?parseFloat(v):undefined); show(res); }
      async function executeRebalance(){ show(await window.pywebview.api.execute_rebalance()); }
      async function doTransaction(){ const t=document.getElementById('tx_ticker').value; const a=document.getElementById('tx_action').value; const s=document.getElementById('tx_shares').value; const p=document.getElementById('tx_price').value; show(await window.pywebview.api.execute_transaction(t,a,s,p?parseFloat(p):null)); }
      async function setWeights(){ const v=document.getElementById('weights').value; show(await window.pywebview.api.set_weights(v)); }
    </script>
  </body>
</html>
"""


def start_gui():
    api = Api()
    window = webview.create_window('Portfolio Rebalancer', html=HTML, js_api=api, width=900, height=800)
    webview.start(gui='gtk', debug=True)


if __name__ == '__main__':
    # run GUI in main thread
    start_gui()
