import ccxt
import pandas as pd
import ta
import time

# تنظیمات صرافی بایبیت تست نت و کلیدهای API
api_key = 'YOUR_TESTNET_API_KEY'
api_secret = 'YOUR_TESTNET_API_SECRET'
exchange = ccxt.bybit({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

# تنظیمات استراتژی
symbols = ['BTC/USDT', 'ETH/USDT', 'XRP/USDT', 'LTC/USDT', 'ADA/USDT']  # لیست جفت ارزهای مورد نظر
timeframe = '5m'  # تایم فریم مناسب برای اسکلپینگ
amount = 0.001  # مقدار خرید و فروش
stop_loss_percent = 0.5  # حد ضرر به درصد
take_profit_ratio = 2  # نسبت حد سود به حد ضرر

def fetch_data(symbol):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def get_signals(df):
    # محاسبه میانگین‌های متحرک
    df['sma_fast'] = df['close'].rolling(window=9).mean()
    df['sma_slow'] = df['close'].rolling(window=21).mean()
    
    # محاسبه RSI
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    
    # سیگنال‌های کندل استیک
    df['bullish_engulfing'] = (df['open'] < df['close'].shift(1)) & (df['close'] > df['open'].shift(1)) & (df['open'] > df['close'].shift(1)) & (df['close'] < df['open'].shift(1))
    df['bearish_engulfing'] = (df['open'] > df['close'].shift(1)) & (df['close'] < df['open'].shift(1)) & (df['open'] < df['close'].shift(1)) & (df['close'] > df['open'].shift(1))

    last_row = df.iloc[-1]
    buy_signal = last_row['bullish_engulfing'] and last_row['sma_fast'] > last_row['sma_slow'] and last_row['rsi'] < 30
    sell_signal = last_row['bearish_engulfing'] and last_row['sma_fast'] < last_row['sma_slow'] and last_row['rsi'] > 70
    
    return buy_signal, sell_signal

def execute_trade(symbol, signal, price):
    if signal == 'buy':
        order = exchange.create_market_buy_order(symbol, amount)
        print(f'Buy Order: {order} for {symbol}')
        stop_loss = price * (1 - stop_loss_percent / 100)
        take_profit = price * (1 + (take_profit_ratio * stop_loss_percent) / 100)
        print(f'Stop Loss: {stop_loss}, Take Profit: {take_profit}')
    elif signal == 'sell':
        order = exchange.create_market_sell_order(symbol, amount)
        print(f'Sell Order: {order} for {symbol}')
        stop_loss = price * (1 + stop_loss_percent / 100)
        take_profit = price * (1 - (take_profit_ratio * stop_loss_percent) / 100)
        print(f'Stop Loss: {stop_loss}, Take Profit: {take_profit}')

def trade():
    for symbol in symbols:
        df = fetch_data(symbol)
        buy_signal, sell_signal = get_signals(df)
        last_price = df['close'].iloc[-1]
        
        if buy_signal:
            execute_trade(symbol, 'buy', last_price)
        elif sell_signal:
            execute_trade(symbol, 'sell', last_price)

while True:
    trade()
    time.sleep(60)  # به مدت یک دقیقه صبر کنید (بسته به تایم فریم انتخابی)2