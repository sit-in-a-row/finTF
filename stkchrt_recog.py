import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from scipy.stats import linregress

# Function to find local maxima and minima
def local_extrema(series, order=1):
    local_max = series[(series.shift(order) < series) & (series.shift(-order) < series)]
    local_min = series[(series.shift(order) > series) & (series.shift(-order) > series)]
    # print(series)
    # print(local_max)
    return local_max, local_min

# Function to detect Double Top pattern
def detect_double_top(data):
    peaks, _ = local_extrema(data['Close'])
    pattern = []
    for i in range(len(peaks)-1):
        peak1 = peaks.iloc[i]
        peak2 = peaks.iloc[i+1]
        time_diff = (peaks.index[i+1] - peaks.index[i]).days
        price_diff = abs(peak1 - peak2) / peak1
        if price_diff < 0.01 and 5 <= time_diff <= 60:
            pattern.append((peaks.index[i], peaks.index[i+1]))
    return pattern

# Function to detect Double Bottom pattern
def detect_double_bottom(data):
    _ , peaks = local_extrema(data['Close'])
    pattern = []
    for i in range(len(peaks)-1):
        peak1 = peaks.iloc[i]
        peak2 = peaks.iloc[i+1]
        time_diff = (peaks.index[i+1] - peaks.index[i]).days
        price_diff = abs(peak1 - peak2) / peak1
        if price_diff < 0.01 and 5 <= time_diff <= 60:
            pattern.append((peaks.index[i], peaks.index[i+1]))
    return pattern

# Function to detect Head and Shoulders pattern
def detect_head_and_shoulders(data):
    peaks, _ = local_extrema(data['Close'])
    pattern = []
    for i in range(1, len(peaks)-1):
        left_shoulder = peaks.iloc[i-1]
        head = peaks.iloc[i]
        right_shoulder = peaks.iloc[i+1]
        ls_idx = peaks.index[i-1]
        h_idx = peaks.index[i]
        rs_idx = peaks.index[i+1]
        if head > left_shoulder and head > right_shoulder:
            height_diff = abs(left_shoulder - right_shoulder) / left_shoulder
            if height_diff < 0.015:
                pattern.append((ls_idx, h_idx, rs_idx))
    return pattern

# Function to detect Triangle pattern
def detect_triangle(data, ra=5):
    # Select recent data
    max_peak, min_peak = local_extrema(data['Close'])
    l = min(len(min_peak), len(max_peak))
    pattern = []
    for i in range (0, l-ra):
        highs = max_peak[i:i+ra]
        lows = min_peak[i:i+ra]
        highs_avg = highs.mean()
        lows_avg = lows.mean()
        flag = False
        for j in range(0, ra):
            highs_diff = highs[j] - highs_avg
            lows_diff = lows[j] - lows_avg
            if abs(highs_diff) > 70:
                flag = True
            if abs(lows_diff) > 70:
                flag = True
        
        if (flag):
            continue

        high_indices = highs.index.map(lambda x: x.toordinal())
        low_indices = lows.index.map(lambda x: x.toordinal())

        # Perform linear regression on highs (resistance) and lows (support)
        resistance_slope, _, _, _, _ = linregress(high_indices, highs)
        support_slope, _, _, _, _ = linregress(low_indices, lows)

        # Check for convergence
        if resistance_slope < 0.2 and resistance_slope > -0.2 and support_slope > 0:
            # Ascending triangle
            pattern.append((highs.index[0], lows.index[0], "Asc", highs.index[ra-1], lows.index[ra-1]))
        elif resistance_slope < 0 and support_slope < 0.2 and support_slope > -0.2:
            # Descending triangle
            pattern.append((highs.index[0], lows.index[0], "Desc", highs.index[ra-1], lows.index[ra-1]))
        elif resistance_slope < 0 and support_slope > 0:
            # Symmetrical triangle
            pattern.append((highs.index[0], lows.index[0], "Sym", highs.index[ra-1], lows.index[ra-1]))
        
    
    return pattern

# Fetch historical stock data
# Need to change using the data we own.
ticker = 'TSLA'  # Apple Inc.
data = yf.download(ticker, start='2020-01-01', end='2023-10-01')
# print(data)

# Detect Double Top patterns
double_tops = detect_double_top(data)
# print(double_tops)

# Detect Double Bottom patterns
double_bottom = detect_double_bottom(data)
print(double_bottom)

# Detect Head and Shoulders patterns
head_and_shoulders = detect_head_and_shoulders(data)

# Detect Triangle pattern
triangle = detect_triangle(data)
print (triangle)

# Plot the results
plt.figure(figsize=(14,7))
plt.plot(data['Close'], label='Close Price')

# Plot triangle
index = 1
for t in triangle:
    label_text_high = "triangle " + t[2] + " " + str(index) + " high"
    label_text_low = "triangle " + t[2] + " " + str(index) + " low"
    label_text_high_end = "triangle " + t[2] + " " + str(index) + " high end"
    label_text_low_end = "triangle " + t[2] + " " + str(index) + " low end"
    plt.plot(t[0], data['Close'].loc[t[0]], marker='v', markersize=10, color='yellow', label='Triangle')
    plt.text(t[0], data['Close'].loc[t[0]], label_text_high)
    plt.plot(t[1], data['Close'].loc[t[1]], marker='v', markersize=10, color='yellow', label='Triangle')
    plt.text(t[1], data['Close'].loc[t[1]], label_text_low)
    plt.plot(t[3], data['Close'].loc[t[3]], marker='v', markersize=10, color='yellow', label='Triangle')
    plt.text(t[3], data['Close'].loc[t[3]], label_text_high_end)
    plt.plot(t[4], data['Close'].loc[t[4]], marker='v', markersize=10, color='yellow', label='Triangle')
    plt.text(t[4], data['Close'].loc[t[4]], label_text_low_end)
    index += 1

# Plot Double Tops
index = 1
for dt in double_tops:
    label_text = "Double Top" + str(index)
    plt.plot(dt[0], data['Close'].loc[dt[0]], marker='o', markersize=10, color='red', label='Double Top')
    plt.text(dt[0], data['Close'].loc[dt[0]], label_text)
    plt.plot(dt[1], data['Close'].loc[dt[1]], marker='o', markersize=10, color='red')
    plt.text(dt[1], data['Close'].loc[dt[1]], label_text)
    index += 1

# Plot Double Tops
index = 1
for dt in double_bottom:
    label_text = "Double Bottom" + str(index)
    plt.plot(dt[0], data['Close'].loc[dt[0]], marker='o', markersize=10, color='red', label='Double Bottom')
    plt.text(dt[0], data['Close'].loc[dt[0]], label_text)
    plt.plot(dt[1], data['Close'].loc[dt[1]], marker='o', markersize=10, color='red')
    plt.text(dt[1], data['Close'].loc[dt[1]], label_text)
    index += 1

# Plot Head and Shoulders
index = 1
for hs in head_and_shoulders:
    plt.plot(hs[0], data['Close'].loc[hs[0]], marker='^', markersize=10, color='green', label='Left Shoulder')
    plt.text(hs[0], data['Close'].loc[hs[0]], "Left Shoulder" + str(index))
    plt.plot(hs[1], data['Close'].loc[hs[1]], marker='^', markersize=10, color='blue', label='Head')
    plt.text(hs[1], data['Close'].loc[hs[1]], "Head" + str(index))
    plt.plot(hs[2], data['Close'].loc[hs[2]], marker='^', markersize=15, color='black', label='Right Shoulder')
    plt.text(hs[2], data['Close'].loc[hs[2]], "Right Shoulder" + str(index))


if len(triangle) != 0:
    plt.title(f'{ticker} Stock Price with Detected Patterns (Triangle Pattern Detected)')
else:
    plt.title(f'{ticker} Stock Price with Detected Patterns')

plt.xlabel('Date')
plt.ylabel('Price')
plt.show()