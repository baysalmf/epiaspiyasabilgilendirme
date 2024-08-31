import re
import yfinance as yf
import requests
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import datetime
import locale
now_day = datetime.now()
import seffaflik2 as sf
import matplotlib.dates as mdates

start_date = '2024-07-23'
end_date = '2024-08-30'

brent_symbol = "BZ=F"
coal_symbol = "MTF=F"
ttf_symbol = "TTF=F"
henry_symbol = "HP=F"

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
ttf_history['Close_new'] = ttf_history['Close']* euro_to_usd * 10.55
henry_hub_history = henry_hub_data.history(period="1y")
henry_hub_history['Close_new'] = henry_hub_history['Close']*35.71
last_date_ttf = ttf_history.index[-1]
last_price_ttf = ttf_history['Close'].iloc[-1] * euro_to_usd * 10.55
last_date_henry = henry_hub_history.index[-1]
last_price_henry = henry_hub_history['Close'].iloc[-1] * 35.71
plt.figure(figsize=(14,8))
plt.plot(ttf_history.index, ttf_history['Close_new'], label='TTF Gaz ($/1000sm3)', color='gray')
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

my_mail = 'm.furkan.baysal@hotmail.com'
my_password = 'Zorlu.2024'
def date_converter(date_string):
    new_string = date_string+"T00:00:00+03:00"
    return new_string

def epias_tgt(e_mail, psw):
    url = f'https://giris.epias.com.tr/cas/v1/tickets?username={e_mail}&password={psw}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'text/plain'
    }
    global response
    response = requests.request('POST', url, headers=headers, timeout=30)
    if response.status_code == 200:
        return response.text

def epias_demand(start_date, end_date, tgt, e_mail, psw):
    sd = date_converter(start_date)
    ed = date_converter(end_date)
    url = f'https://seffaflik.epias.com.tr/electricity-service/v1/consumption/data/realtime-consumption?username={e_mail}&password={psw}'

    payload = json.dumps({
        'endDate': ed,
        'startDate': sd,
        'region': 'TR1'
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'TGT': tgt
    }

    response = requests.request('POST', url, headers=headers, data=payload, timeout=30)

    if response.status_code == 200:
        df_consumption = pd.json_normalize(response.json()['items'])
        df_consumption['date'] = pd.to_datetime(df_consumption['date'])
        return df_consumption
    else:
        response.text


def epias_mcp(start_date, end_date, tgt, e_mail, psw):
    sd = date_converter(start_date)
    ed = date_converter(end_date)
    url = f'https://seffaflik.epias.com.tr/electricity-service/v1/markets/dam/data/mcp?username={e_mail}&password={psw}'

    payload = json.dumps({
        'endDate': ed,
        'startDate': sd,
        'region': 'TR1'
    })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'TGT': tgt
    }

    response = requests.request('POST', url, headers=headers, data=payload, timeout=30)

    if response.status_code == 200:
        df_ptf = pd.json_normalize(response.json()['items'])
        df_ptf['date'] = pd.to_datetime(df_ptf['date'])
        return df_ptf.resample('D', on='date').mean()
    else:
        response.text

myTGT = sf.epias_tgt(my_mail, my_password)

df_ptf = sf.epias_mcp(start_date, end_date, myTGT, my_mail, my_password)
df_ptf.drop(['hour', 'priceUsd', 'priceEur'], axis=1, inplace=True)
df_ptf = df_ptf.resample('D', on='date').mean()

df_dmd = sf.epias_demand(start_date, end_date, myTGT, my_mail, my_password)
df_dmd.drop(['time'], axis=1, inplace=True)
df_dmd = df_dmd.resample('D', on='date').sum()

df_merge = df_ptf.merge(df_dmd, on='date')

fig, ax1 = plt.subplots(figsize=(16, 8))

ax1.plot(df_dmd.index, df_dmd['consumption'] / 1000, 'g-', label='Tüketim (GWh)')
ax1.set_xlabel('Tarih')
ax1.set_ylabel('Tüketim (GWh)', color='red')
ax1.set_ylim(0, 1200)
ax1.tick_params(axis='y', labelcolor='red')

# Create a second y-axis for df_ptf
ax2 = ax1.twinx()
ax2.plot(df_ptf.index, df_ptf['price'], 'b-', label='PTF')
ax2.set_ylabel('PTF', color='b')
ax2.set_ylim(0, 5000)
ax2.tick_params(axis='y', labelcolor='b')

# Format x-axis to show dates clearly
ax1.xaxis.set_major_locator(mdates.DayLocator(interval=1))
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
fig.autofmt_xdate()  # Rotate dates for better readability

for date, value in df_ptf['price'].items():
    ax2.annotate(f'{value:.0f}', (date, value), textcoords="offset points", xytext=(0,5), ha='center', color='b')

for date, value in df_dmd['consumption'].items():
    ax1.annotate(f'{value/1000:.0f}', (date, value/1000), textcoords="offset points", xytext=(0,5), ha='center', color='r')

# Show the plot
fig.tight_layout()
plt.title('Gerçekleşen Tük. (GWh) vs PTF')
plt.show()