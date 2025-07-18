# -*- coding: utf-8 -*-
"""Siddesh_Kathavale_20019619ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1KAOhZGHiJ6EjicW5IJ5BLGWhxmwFZLyf
"""

!pip install ta

!pip install yfinance

# Import necessary libraries
import yfinance as yf
import pandas as pd
import numpy as np
import ta  # Technical Analysis library
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from sklearn.metrics import mean_squared_error, r2_score

# Define the function to apply advanced indicators
def apply_advanced_indicators(df):
    df['ADX'] = ta.trend.adx(df['High'], df['Low'], df['Close'], window=14)
    df['Bollinger_hband'] = ta.volatility.bollinger_hband(df['Close'], window=20, window_dev=2)
    df['Bollinger_lband'] = ta.volatility.bollinger_lband(df['Close'], window=20, window_dev=2)
    df['Ichimoku_a'] = ta.trend.ichimoku_a(df['High'], df['Low'])
    df['Ichimoku_b'] = ta.trend.ichimoku_b(df['High'], df['Low'])
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    macd = ta.trend.macd(df['Close'], window_slow=26, window_fast=12)
    macd_signal = ta.trend.macd_signal(df['Close'], window_slow=26, window_fast=12, window_sign=9)
    df['MACD'] = macd
    df['MACD_Signal'] = macd_signal
    df['MACD_Hist'] = macd - macd_signal
    df['Stochastic_k'] = ta.momentum.stoch(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    df['Stochastic_d'] = ta.momentum.stoch_signal(df['High'], df['Low'], df['Close'], window=14, smooth_window=3)
    return df

# Define the function to create a dataset for LSTM
def create_dataset(dataset, time_step=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-time_step-1):
        a = dataset[i:(i+time_step), 0:dataset.shape[1]-1]
        dataX.append(a)
        dataY.append(dataset[i + time_step, -1])
    return np.array(dataX), np.array(dataY)

# Define function to download and process data
def download_and_process_data(ticker, start_date='2014-01-01', end_date='2024-08-01'):
    data = yf.download(ticker, start=start_date, end=end_date)
    data = apply_advanced_indicators(data)
    data = data.dropna()
    return data

# Download and process HDFC data
hdfc_data = download_and_process_data('HDFCBANK.NS')
hdfc_data = hdfc_data.dropna()

# Display the first few rows of the processed HDFC data with advanced indicators
print(hdfc_data.head())

# Scale the data
feature_cols = ['ADX', 'Bollinger_hband', 'Bollinger_lband', 'Ichimoku_a', 'Ichimoku_b', 'RSI', 'MACD', 'MACD_Signal', 'MACD_Hist', 'Stochastic_k', 'Stochastic_d']
scaler = MinMaxScaler()
hdfc_scaled = scaler.fit_transform(hdfc_data[feature_cols + ['Close']])

# Display the first few rows of the scaled data
print(pd.DataFrame(hdfc_scaled, columns=feature_cols + ['Close']).head())

# Save the processed HDFC data with advanced indicators to a CSV file
hdfc_data.to_csv('hdfc_data_with_indicators.csv', index=True)

# Create training dataset for HDFC
time_step = 100
X, y = create_dataset(hdfc_scaled, time_step)
X_reshaped = np.reshape(X, (X.shape[0], X.shape[1], len(feature_cols)))

"""# **LSTM**"""

# Define and compile the LSTM model
model = Sequential()
model.add(LSTM(100, return_sequences=True, input_shape=(time_step, len(feature_cols))))
model.add(Dropout(0.2))
model.add(LSTM(100, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')

# Train the model
model.fit(X_reshaped, y, epochs=50, batch_size=64, verbose=1)

# Fine-tune the model and test on other stocks
tickers = ['HDFCBANK.NS','KOTAKBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS', 'INDUSINDBK.NS', 'BANDHANBNK.NS', 'IDFCFIRSTB.NS', 'PNB.NS', 'RBLBANK.NS', 'YESBANK.NS', 'FEDERALBNK.NS']

results = []

for ticker in tickers:
    stock_data = download_and_process_data(ticker)

    # Scale and prepare the data
    stock_scaled = scaler.transform(stock_data[feature_cols + ['Close']])
    X_stock, y_stock = create_dataset(stock_scaled, time_step)
    X_stock_reshaped = np.reshape(X_stock, (X_stock.shape[0], X_stock.shape[1], len(feature_cols)))

    # Predict and evaluate
    predictions = model.predict(X_stock_reshaped)
    # Create an array with the same number of columns as the scaler was fitted on, filled with zeros
    empty_features = np.zeros((predictions.shape[0], len(feature_cols)))
    # Insert predictions into the last column (the Close column)
    combined_predictions = np.concatenate([empty_features, predictions], axis=-1)
    # Perform inverse transform
    predictions_inverse = scaler.inverse_transform(combined_predictions)[:, -1]

    true_values = stock_data['Close'].values[time_step + 1:]
    true_values = true_values[:len(predictions_inverse)]  # Match length of true values and predictions
    rmse = np.sqrt(mean_squared_error(true_values, predictions_inverse))
    r2 = r2_score(true_values, predictions_inverse)
    rmsle = np.sqrt(np.mean((np.log1p(predictions_inverse) - np.log1p(true_values))**2))

    results.append((ticker, rmse, r2, rmsle))
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")

# Print results
for result in results:
    ticker, rmse, r2, rmsle = result
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")

"""# **GRU Model**"""

from keras.models import Sequential
from keras.layers import GRU, Dense, Dropout

# Define and compile the GRU model
gru_model = Sequential()
gru_model.add(GRU(100, return_sequences=True, input_shape=(X.shape[1], X.shape[2])))
gru_model.add(Dropout(0.2))
gru_model.add(GRU(100, return_sequences=False))
gru_model.add(Dropout(0.2))
gru_model.add(Dense(1))
gru_model.compile(optimizer='adam', loss='mse')

# Train the model
gru_model.fit(X_reshaped, y, epochs=50, batch_size=64, verbose=1)

from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

# Make predictions with the GRU model
gru_predictions = gru_model.predict(X_reshaped)
gru_predictions_inverse = scaler.inverse_transform(np.concatenate([np.zeros((gru_predictions.shape[0], len(feature_cols))), gru_predictions], axis=-1))[:, -1]

# Inverse transform the actual y values
y_actual_inverse = scaler.inverse_transform(np.concatenate([np.zeros((y.shape[0], len(feature_cols))), y.reshape(-1, 1)], axis=-1))[:, -1]

# Calculate RMSE and R^2
gru_rmse = np.sqrt(mean_squared_error(y_actual_inverse, gru_predictions_inverse))
gru_r2 = r2_score(y_actual_inverse, gru_predictions_inverse)

print(f'GRU - RMSE: {gru_rmse}, R^2: {gru_r2}')

# Import necessary libraries
from sklearn.metrics import mean_squared_error, r2_score

# Fine-tune the model and test on other stocks
tickers = ['HDFCBANK.NS','KOTAKBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS', 'INDUSINDBK.NS', 'BANDHANBNK.NS', 'IDFCFIRSTB.NS', 'PNB.NS', 'RBLBANK.NS', 'YESBANK.NS', 'FEDERALBNK.NS']

results = []

for ticker in tickers:
    stock_data = download_and_process_data(ticker)

    # Scale and prepare the data
    stock_scaled = scaler.transform(stock_data[feature_cols + ['Close']])
    X_stock, y_stock = create_dataset(stock_scaled, time_step)
    X_stock_reshaped = np.reshape(X_stock, (X_stock.shape[0], X_stock.shape[1], len(feature_cols)))

    # Predict and evaluate using the GRU model
    predictions = gru_model.predict(X_stock_reshaped)

    # Prepare for inverse transform
    empty_features = np.zeros((predictions.shape[0], len(feature_cols)))
    combined_predictions = np.concatenate([empty_features, predictions], axis=-1)
    predictions_inverse = scaler.inverse_transform(combined_predictions)[:, -1]

    # Match length of true values and predictions
    true_values = stock_data['Close'].values[time_step + 1:]
    true_values = true_values[:len(predictions_inverse)]

    # Calculate metrics
    rmse = np.sqrt(mean_squared_error(true_values, predictions_inverse))
    r2 = r2_score(true_values, predictions_inverse)
    rmsle = np.sqrt(np.mean((np.log1p(predictions_inverse) - np.log1p(true_values))**2))

    # Store results
    results.append((ticker, rmse, r2, rmsle))
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")

# Print results
for result in results:
    ticker, rmse, r2, rmsle = result
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")

"""# **Tune-GRU**"""

from keras.models import Sequential
from keras.layers import GRU, Dense, Dropout

# Define and compile the GRU model
gru_model = Sequential()
gru_model.add(GRU(100, return_sequences=True, input_shape=(X.shape[1], X.shape[2])))
gru_model.add(Dropout(0.2))
gru_model.add(GRU(100, return_sequences=False))
gru_model.add(Dropout(0.2))
gru_model.add(Dense(1))
gru_model.compile(optimizer='adam', loss='mse')

# Train the model
gru_model.fit(X_reshaped, y, epochs=50, batch_size=64, verbose=1)

# Save the model again
gru_model.save('new_gru_model.h5')

# Fine-tune the model and test on other stocks
tickers = ['HDFCBANK.NS','KOTAKBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS', 'INDUSINDBK.NS', 'BANDHANBNK.NS', 'IDFCFIRSTB.NS', 'PNB.NS', 'RBLBANK.NS', 'YESBANK.NS', 'FEDERALBNK.NS']

results = []

for ticker in tickers:
    stock_data = download_and_process_data(ticker)

    # Scale and prepare the data
    stock_scaled = scaler.transform(stock_data[feature_cols + ['Close']])
    X_stock, y_stock = create_dataset(stock_scaled, time_step)
    X_stock_reshaped = np.reshape(X_stock, (X_stock.shape[0], X_stock.shape[1], len(feature_cols)))

    # Predict and evaluate using the GRU model
    predictions = gru_model.predict(X_stock_reshaped)

    # Prepare for inverse transform
    empty_features = np.zeros((predictions.shape[0], len(feature_cols)))
    combined_predictions = np.concatenate([empty_features, predictions], axis=-1)
    predictions_inverse = scaler.inverse_transform(combined_predictions)[:, -1]

    # Match length of true values and predictions
    true_values = stock_data['Close'].values[time_step + 1:]
    true_values = true_values[:len(predictions_inverse)]

    # Calculate metrics
    rmse = np.sqrt(mean_squared_error(true_values, predictions_inverse))
    r2 = r2_score(true_values, predictions_inverse)
    rmsle = np.sqrt(np.mean((np.log1p(predictions_inverse) - np.log1p(true_values))**2))

    # Store results
    results.append((ticker, rmse, r2, rmsle))
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")

# Print results
for result in results:
    ticker, rmse, r2, rmsle = result
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")

# Save the trained GRU model
gru_model.save('gru_model.h5')

from keras.callbacks import EarlyStopping

# Train the model
history = model.fit(X_reshaped, y, epochs=50, batch_size=32, validation_split=0.2, verbose=1, callbacks=[EarlyStopping(monitor='val_loss', patience=5)])

from keras.optimizers import Adam
from keras.callbacks import EarlyStopping
# Define and compile the GRU model with the best hyperparameters
model = Sequential()
model.add(GRU(128, return_sequences=True, input_shape=(time_step, len(feature_cols))))
model.add(Dropout(0.2))
model.add(GRU(64, return_sequences=False))
model.add(Dropout(0.2))
model.add(Dense(1))

# Compile the model
optimizer = Adam(learning_rate=0.001)
model.compile(optimizer=optimizer, loss='mse')

# Train the model
history = model.fit(X_reshaped, y, epochs=50, batch_size=32, validation_split=0.2, verbose=1, callbacks=[EarlyStopping(monitor='val_loss', patience=5)])

# Evaluate the model across all bank stocks
tickers = ['HDFCBANK.NS','KOTAKBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS', 'INDUSINDBK.NS', 'BANDHANBNK.NS', 'IDFCFIRSTB.NS', 'PNB.NS', 'RBLBANK.NS', 'YESBANK.NS', 'FEDERALBNK.NS']

results = []

for ticker in tickers:
    stock_data = download_and_process_data(ticker)

    # Scale and prepare the data
    stock_scaled = scaler.transform(stock_data[feature_cols + ['Close']])
    X_stock, y_stock = create_dataset(stock_scaled, time_step)
    X_stock_reshaped = np.reshape(X_stock, (X_stock.shape[0], X_stock.shape[1], len(feature_cols)))

    # Predict and evaluate
    predictions = model.predict(X_stock_reshaped)
    empty_features = np.zeros((predictions.shape[0], len(feature_cols)))
    combined_predictions = np.concatenate([empty_features, predictions], axis=-1)
    predictions_inverse = scaler.inverse_transform(combined_predictions)[:, -1]

    true_values = stock_data['Close'].values[time_step + 1:]
    true_values = true_values[:len(predictions_inverse)]
    rmse = np.sqrt(mean_squared_error(true_values, predictions_inverse))
    r2 = r2_score(true_values, predictions_inverse)
    rmsle = np.sqrt(np.mean((np.log1p(predictions_inverse) - np.log1p(true_values))**2))

    results.append((ticker, rmse, r2, rmsle))
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")

# Print results
for result in results:
    ticker, rmse, r2, rmsle = result
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")

"""# **ARIMA model**"""

!pip install statsmodels

import statsmodels.api as sm

# Fit ARIMA model (p, d, q) needs to be tuned according to the dataset
arima_model = sm.tsa.ARIMA(hdfc_data['Close'], order=(5, 1, 0))
arima_result = arima_model.fit()

# Summary of the model
print(arima_result.summary())

# Make predictions
arima_forecast = arima_result.forecast(steps=30)

import yfinance as yf
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm

# Define function to download and process data
def download_data(ticker, start_date='2018-01-01', end_date='2023-01-01'):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

# List of bank tickers
tickers = ['HDFCBANK.NS', 'KOTAKBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS',
           'INDUSINDBK.NS', 'BANDHANBNK.NS', 'IDFCFIRSTB.NS', 'PNB.NS',
           'RBLBANK.NS', 'YESBANK.NS', 'FEDERALBNK.NS']

results = []

for ticker in tickers:
    # Download and process data for each bank
    data = download_data(ticker)

    # Fit ARIMA model (p, d, q) needs to be tuned according to the dataset
    try:
        arima_model = sm.tsa.ARIMA(data['Close'], order=(5, 1, 0))
        arima_result = arima_model.fit()

        # Make predictions
        forecast_steps = 30
        arima_forecast = arima_result.forecast(steps=forecast_steps)
        arima_forecast = np.array(arima_forecast)

        # Calculate true values for comparison
        true_values = data['Close'][-forecast_steps:].values

        # Calculate RMSE and R²
        rmse = np.sqrt(mean_squared_error(true_values, arima_forecast))
        r2 = r2_score(true_values, arima_forecast)

        results.append((ticker, rmse, r2))
        print(f"{ticker} - RMSE: {rmse}, R^2: {r2}")

    except Exception as e:
        print(f"Error with {ticker}: {e}")
        results.append((ticker, None, None))

# Print results
for result in results:
    ticker, rmse, r2 = result
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}")

"""# **SARIMA model**"""

# Fit SARIMA model (p, d, q)(P, D, Q, s) needs to be tuned
sarima_model = sm.tsa.SARIMAX(hdfc_data['Close'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
sarima_result = sarima_model.fit()

# Summary of the model
print(sarima_result.summary())

# Make predictions
sarima_forecast = sarima_result.forecast(steps=30)

import yfinance as yf
import statsmodels.api as sm
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score

# Function to download and process data
def download_and_process_data(ticker, start_date='2018-01-01', end_date='2023-01-01'):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

# Define a function to evaluate SARIMA for a given stock ticker
def evaluate_sarima(ticker):
    stock_data = download_and_process_data(ticker)
    stock_data = stock_data.dropna()

    # Fit SARIMA model
    sarima_model = sm.tsa.SARIMAX(stock_data['Close'], order=(1, 1, 1), seasonal_order=(1, 1, 1, 12))
    sarima_result = sarima_model.fit(disp=False)

    # Make predictions
    sarima_forecast = sarima_result.get_forecast(steps=len(stock_data))
    predicted_close = sarima_forecast.predicted_mean
    true_values = stock_data['Close'].values

    # Calculate performance metrics
    rmse = np.sqrt(mean_squared_error(true_values, predicted_close))
    r2 = r2_score(true_values, predicted_close)
    rmsle = np.sqrt(np.mean((np.log1p(predicted_close) - np.log1p(true_values))**2))

    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")
    return rmse, r2, rmsle

# List of bank tickers
tickers = ['HDFCBANK.NS','KOTAKBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS',
           'INDUSINDBK.NS', 'BANDHANBNK.NS', 'IDFCFIRSTB.NS', 'PNB.NS', 'RBLBANK.NS',
           'YESBANK.NS', 'FEDERALBNK.NS']

# Evaluate SARIMA for all the banks
sarima_results = []
for ticker in tickers:
    result = evaluate_sarima(ticker)
    sarima_results.append((ticker, *result))

# Print all results
for result in sarima_results:
    ticker, rmse, r2, rmsle = result
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")

"""# **Prophet model**"""

!pip install prophet

from prophet import Prophet

# Prepare data for Prophet
prophet_df = hdfc_data.reset_index()[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})

# Fit Prophet model
prophet_model = Prophet()
prophet_model.fit(prophet_df)

# Make predictions
future = prophet_model.make_future_dataframe(periods=30)
prophet_forecast = prophet_model.predict(future)

# Plot forecast
prophet_model.plot(prophet_forecast)

from prophet import Prophet
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.metrics import mean_squared_error, r2_score

# Function to download and process data
def download_and_process_data(ticker, start_date='2018-01-01', end_date='2023-01-01'):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

# Define a function to evaluate Prophet for a given stock ticker
def evaluate_prophet(ticker):
    stock_data = download_and_process_data(ticker)
    stock_data = stock_data.dropna()

    # Prepare data for Prophet
    prophet_df = stock_data.reset_index()[['Date', 'Close']].rename(columns={'Date': 'ds', 'Close': 'y'})

    # Fit Prophet model
    prophet_model = Prophet()
    prophet_model.fit(prophet_df)

    # Make predictions
    future = prophet_model.make_future_dataframe(periods=30)
    prophet_forecast = prophet_model.predict(future)

    # Extract predictions and calculate performance metrics
    predicted_close = prophet_forecast['yhat'].values[:len(stock_data)]
    true_values = stock_data['Close'].values

    rmse = np.sqrt(mean_squared_error(true_values, predicted_close))
    r2 = r2_score(true_values, predicted_close)
    rmsle = np.sqrt(np.mean((np.log1p(predicted_close) - np.log1p(true_values))**2))

    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")
    return rmse, r2, rmsle

# List of bank tickers
tickers = ['HDFCBANK.NS','KOTAKBANK.NS', 'ICICIBANK.NS', 'AXISBANK.NS', 'SBIN.NS',
           'INDUSINDBK.NS', 'BANDHANBNK.NS', 'IDFCFIRSTB.NS', 'PNB.NS', 'RBLBANK.NS',
           'YESBANK.NS', 'FEDERALBNK.NS']

# Evaluate Prophet for all the banks
prophet_results = []
for ticker in tickers:
    result = evaluate_prophet(ticker)
    prophet_results.append((ticker, *result))

# Print all results
for result in prophet_results:
    ticker, rmse, r2, rmsle = result
    print(f"{ticker} - RMSE: {rmse}, R^2: {r2}, RMSLE: {rmsle}")

"""# **Sentiment Analysis **"""

import requests
from bs4 import BeautifulSoup

# Define the URL
url = "https://finance.yahoo.com/quote/HDFCBANK.NS/news/"

# Set headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Referer': 'https://finance.yahoo.com/',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

# Send the request
response = requests.get(url, headers=headers)

# Check the status code
print(response.status_code)  # Expect 200 for a successful request

# Parse the HTML content if the request was successful
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    headlines = soup.find_all('h3', class_='clamp')
    for headline in headlines:
        print(headline.text)
else:
    print("Failed to retrieve the page")

import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download the VADER lexicon
nltk.download('vader_lexicon')

# Initialize VADER Sentiment Analyzer
sia = SentimentIntensityAnalyzer()

# The rest of your code remains unchanged

import requests
from bs4 import BeautifulSoup

# List of BANKNIFTY stock symbols
banknifty_stocks = [
    "HDFCBANK.NS", "KOTAKBANK.NS", "ICICIBANK.NS", "AXISBANK.NS", "SBIN.NS",
    "INDUSINDBK.NS", "BANDHANBNK.NS", "IDFCFIRSTB.NS", "PNB.NS", "RBLBANK.NS",
    "YESBANK.NS", "FEDERALBNK.NS"
]


# Define a function to fetch and analyze news sentiment for each bank
def fetch_and_analyze_sentiment(stock_symbol):
    url = f"https://finance.yahoo.com/quote/{stock_symbol}/news/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Referer': 'https://finance.yahoo.com/',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        headline = soup.find('h3', class_='clamp')  # Get the first headline
        if headline:
            text = headline.text
            sentiment = sia.polarity_scores(text)
            return stock_symbol, text, sentiment
        else:
            return stock_symbol, "No headline found", None
    else:
        return stock_symbol, "Failed to retrieve the page", None

# Iterate through the bank stocks and print the sentiment analysis
for stock in banknifty_stocks:
    stock_symbol, headline, sentiment = fetch_and_analyze_sentiment(stock)
    print(f"Stock: {stock_symbol}")
    print(f"Headline: {headline}")
    print(f"Sentiment: {sentiment}\n")