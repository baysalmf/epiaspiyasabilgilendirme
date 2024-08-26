import yfinance as yf
import requests
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime
import locale
now_day = datetime.now()


params = {
    'startDate': '2024-07-24T00:00:00+03:00',
    'endDate': '2024-08-25T23:59:59+03:00'
}

brent_symbol = "BZ=F"
coal_symbol = "MTF=F"
ttf_symbol = "TTF=F"
henry_symbol = "HH=F"

brent_data = yf.Ticker(brent_symbol)
brent_history = brent_data.history(period="1y")
coal_data = yf.Ticker(coal_symbol)
coal_history = coal_data.history(period="1y")
last_date_brent = brent_history.index[-1]
last_price_brent = brent_history['Close'].iloc[-1]
last_date_coal = coal_history.index[-1]
last_price_coal = coal_history['Close'].iloc[-1]

plt.figure(figsize=(12,8))
plt.plot(brent_history.index, brent_history['Close'], label='Brent Petrol($/varil)', color='red')
plt.scatter(last_date_brent, last_price_brent, color='red')
plt.text(last_date_brent, last_price_brent, f'{last_price_brent:.2f} USD', color='red', fontsize=12, ha='left', va='bottom')
plt.plot(coal_history.index, coal_history['Close'], label='Coal($/ton)', color='gray')
plt.scatter(last_date_coal, last_price_coal, color='gray')
plt.text(last_date_coal, last_price_coal, f'{last_price_coal:.2f} USD', color='gray', fontsize=12, ha='left', va='bottom')
plt.title(f"Emtia Fiyatları - {datetime.strftime(now_day, '%D')}")
plt.xlabel('Tarih')
plt.ylabel('Fiyat ($)')
plt.legend()
plt.grid(True)
plt.show()

url = 'https://api.exchangerate-api.com/v4/latest/EUR'
try:
    response = requests.get(url)
    data = response.json()
    euro_to_usd = data['rates']['USD']
except requests.exceptions.RequestException as e:
    print(f"Veri çekilirken bir hata oluştu: {e}")

ttf_data = yf.Ticker(ttf_symbol)
henry_hub_data = yf.Ticker(henry_symbol)
ttf_history = ttf_data.history(period="1y")
ttf_history['Close_new'] = ttf_history['Close']* euro_to_usd *10.55
henry_hub_history = henry_hub_data.history(period="1y")
henry_hub_history['Close_new'] = henry_hub_history['Close']* euro_to_usd *10.55
last_date_ttf = ttf_history.index[-1]
last_price_ttf = ttf_history['Close'].iloc[-1] * euro_to_usd * 10.55
last_date_henry = henry_hub_history.index[-1]
last_price_henry = henry_hub_history['Close'].iloc[-1] * euro_to_usd * 10.55
plt.figure(figsize=(14,8))
plt.plot(ttf_history.index, ttf_history['Close_new'], label='TFF Gaz ($/1000sm3)', color='gray')
plt.scatter(last_date_ttf, last_price_ttf, color='gray')
plt.text(last_date_ttf, last_price_ttf, f'{last_price_ttf:.2f}', color='gray', fontsize=12, ha='left', va='bottom')
plt.plot(henry_hub_history.index, henry_hub_history['Close_new'], label='Henry Gaz ($/1000sm3)', color='blue')
plt.scatter(last_date_henry, last_price_henry, color='blue')
plt.text(last_date_henry, last_price_henry, f'{last_price_henry:.2f}', color='blue', fontsize=12, ha='left', va='bottom')
plt.title(f"Emtia Fiyatları - {datetime.strftime(now_day, '%D')}")
plt.xlabel('Tarih')
plt.ylabel('Fiyat($)')
plt.legend()
plt.grid(True)
plt.show()

gerceklesen_url = 'https://seffaflik.epias.com.tr/transparency/service/consumption/real-time-consumption'
gerceklesen_response = requests.get(gerceklesen_url, params=params)
gerceklesen_df = pd.DataFrame.from_dict(gerceklesen_response.json()['body']['hourlyConsumptions'])
gerceklesen_df['date']= pd.to_datetime(gerceklesen_df['date'])
gerceklesen_gunluk = gerceklesen_df.resample('D', on='date').sum()/1000

ptf_url = 'https://seffaflik.epias.com.tr/transparency/service/market/mcp-smp'
ptf_response = requests.get(ptf_url, params=params)
ptf_df = pd.DataFrame.from_dict(ptf_response.json()['body']['mcpSmps'])
ptf_df['date'] = pd.to_datetime(ptf_df['date'])
columns_to_drop = ['smp', 'smpDirection', 'mcpState']
ptf_df.drop(columns=columns_to_drop, inplace=True)
ptf_gunluk = ptf_df.resample('D', on='date').mean()

fig, ax1 = plt.subplots(figsize= (20, 6))

color = 'tab:blue'
ax1.set_xlabel('TARİH')
ax1.set_ylabel('TÜKETİM(GWh)', color=color)
ax1.plot(gerceklesen_gunluk.index, gerceklesen_gunluk, color=color, label='Consumption(MWh)')
ax1.tick_params(axis='y', labelcolor=color)

for i, v in gerceklesen_gunluk.iterrows():
    ax1.text(i, v[0], f'{v[0]:.0f}', ha='center', va='bottom', color=color)

ax2 = ax1.twinx()
color = 'tab:red'
ax2.set_ylabel('PTF (TL/MWh)', color=color)
ax2.plot(ptf_gunluk.index, ptf_gunluk, color=color, label='PTF (TL/MWh)')
ax2.tick_params(axis='y', labelcolor=color)

for i, v in ptf_gunluk.iterrows():
    ax2.text(i, v[0], f'{v[0]:.2f}', ha='center', va='bottom', color=color)

ax1.set_ylim(0, 1400)
plt.title(f"TR GERÇEKLEŞEN TÜKETİM-PTF - {datetime.strftime(now_day, '%d/%m/%Y')}")
plt.show()