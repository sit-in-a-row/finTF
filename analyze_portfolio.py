import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import csv
from datetime import datetime
import json

def fetch_data(stocks, start_date, end_date):
    """Fetch historical adjusted closing prices for given stocks."""
    data = yf.download(stocks, start=start_date, end=end_date)['Adj Close']
    return data

def calculate_portfolio_returns(returns, weights):
    """Calculate daily portfolio returns."""
    portfolio_returns = returns.dot(weights)
    return portfolio_returns

def calculate_sharpe_ratio(portfolio_return, portfolio_volatility, risk_free_rate):
    """Calculate Sharpe Ratio."""
    sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
    return sharpe_ratio

def calculate_var(portfolio_returns, confidence_level):
    """Calculate Value at Risk (VaR) using historical simulation."""
    VaR = -np.percentile(portfolio_returns, (1 - confidence_level) * 100)
    return VaR

def calculate_es(portfolio_returns, VaR):
    """Calculate Expected Shortfall (ES)."""
    ES = -portfolio_returns[portfolio_returns <= -VaR].mean()
    return ES

#calculates by summing up the beta of each stocks
def calculate_beta(stocks, returns, weights, market_index, risk_free_rate = '0.03'):
    market_var = market_index.var();
    beta_sum = 0;
    for i in range(0, len(stocks)):
        # print(stocks[i])
        # print(returns[stocks[i]]);
        # print(market_index)
        new_returns = returns[stocks[i]]
        s_cov = np.cov(returns[stocks[i]], market_index)[0][1];
        beta_sum += weights[i] * (s_cov / market_var);

    return beta_sum;    

#calculates the beta from the portfolio return itself
def cb(portfolio_returns, market_index):
    market_var = market_index.var();
    p_cov = np.cov(portfolio_returns, market_index)[0][1];

    return p_cov / market_var

def get_common_date(stocks):
    
    start_year = 2017
    stop_year = datetime.now().year-1
    months = ['01', '02', '03', '04', '05','06','07','08', '09', '10', '11', '12']

    answer = []
    ans_year = 2017
    ans_month = 0
    flag_found = False
    for i in stocks:
        flag_found = False
        for j in range(start_year, stop_year):
            for k in range(0,12):
                file_name = str(j) + '.' + months[k] + "_" + i + '.csv'
                file_path = './store_data/raw/market_data/price/' + i + '/' + str(j) + '.' + months[k] + "/" + file_name
                try:
                    csvfile = open(file_path, newline='')
                    csvfile.close()
                    flag_found = True
                    if (ans_year < j):
                        ans_year = j
                        ans_month = k
                    elif (ans_year == j):
                        ans_year = j
                        ans_month = max(k, ans_month)
                    break
                except:
                    continue
            if flag_found == True:
                break

    answer.append(ans_year)
    answer.append(ans_month)
    return answer

def get_data(stocks, cd):

    start_year = cd[0] #get_common_date(stocks)
    stop_year = datetime.now().year-1
    months = ['01', '02', '03', '04', '05','06','07','08', '09', '10', '11', '12']
    initial = cd[1]
    data_dict = {}
    list_date = []
    date_flag = False
    for i in stocks:
        list_closed = []
        initial = cd[1]
        for j in range(start_year, stop_year):
            for k in range(initial, 12):
                file_name = str(j) + '.' + months[k] + "_" + i + '.csv'
                file_path = './store_data/raw/market_data/price/' + i + '/' + str(j) + '.' + months[k] + "/" + file_name
                try:
                    csvfile = open(file_path, newline='')
                    stockreader = csv.reader(csvfile)
                    for z in stockreader:
                        if (z[4].isnumeric()):
                            if (date_flag == False):
                                datetime_obj = datetime.strptime(z[0], '%Y-%m-%d').date()
                                list_date.append(datetime_obj)
                            list_closed.append(int(z[4]))
                    csvfile.close()
                except:
                    print("NO FILE: " + file_path)
                    continue
            initial = 0
        date_flag = True
        data_dict[i] = list_closed


    df = pd.DataFrame(data=data_dict, index=list_date)
    return df


def analyze_portfolio(stocks, weights):
    months = ['01', '02', '03', '04', '05','06','07','08', '09', '10', '11', '12']
    cd = get_common_date(stocks)
    if (len(cd) == 0):
        print("STOCK DOESN'T EXIST")
        return

    # Fetch historical adjusted closing prices
    data = get_data(stocks, cd) 
    #data = fetch_data(stocks, start_date='2017-01-01', end_date='2024-01-01')
    # print(data)
    # print(type(data.index[0]))
    start_string = str(cd[0]) + '-' + months[cd[1]] + '-01'
    market_index = yf.download('^KS11', start=start_string, end="2024-01-01")['Adj Close'].pct_change().dropna()
    market_index.index = market_index.index.date
    # Calculate daily returns
    returns = data.pct_change().dropna()
    common_dates = data.index.intersection(market_index.index);
    returns = returns.loc[common_dates]
    market_index = market_index.loc[common_dates]

    # Calculate daily portfolio returns
    portfolio_returns = calculate_portfolio_returns(returns, weights)

    # Calculate annualized expected returns and covariance matrix
    expected_returns = returns.mean() * 252  # Assuming 252 trading days
    cov_matrix = returns.cov() * 252  # Annualize covariance matrix


    # Calculate portfolio expected return
    portfolio_return = np.dot(weights, expected_returns)

    # Calculate portfolio volatility (standard deviation)
    portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

    # Assume a risk-free rate (e.g., 2%)
    risk_free_rate = 0.037

    # Calculate Sharpe Ratio
    sharpe_ratio = calculate_sharpe_ratio(portfolio_return, portfolio_volatility, risk_free_rate)

    # Calculate VaR and ES
    confidence_level = 0.95  # 95% confidence level
    VaR = calculate_var(portfolio_returns, confidence_level)
    ES = calculate_es(portfolio_returns, VaR)

    time_horizon = 1# days
    VaR *= np.sqrt(time_horizon)
    ES *= np.sqrt(time_horizon)


    portfolio_beta = calculate_beta(stocks, returns, weights, market_index)
    b = cb(portfolio_returns, market_index)

    # Display the results
    print(f"Portfolio Expected Annual Return: {portfolio_return:.2%}")
    print(f"Portfolio Annual Volatility: {portfolio_volatility:.2%}")
    print(f"Portfolio Sharpe Ratio: {sharpe_ratio:.2f}")
    print("Portfolio Beta: {:.4f}".format(portfolio_beta))
    print("Portfolio Beta from portfolio: {:.4f}".format(b))
    print(f"Portfolio VaR (95% confidence): {VaR:.2%}")
    print(f"Portfolio Expected Shortfall (ES): {ES:.2%}")

    result_dict = {"Expected Annual Return": portfolio_return, "Annual Volatility": portfolio_volatility, "Sharpe Ratio": sharpe_ratio, "Beta": portfolio_beta, "VaR(0.95 confidence)": VaR, "ES": ES}
    with open("result.json", "w") as jfile:
        json.dump(result_dict, jfile)
    
if __name__ == "__main__":
        # Define your portfolio
    stocks = ['035720', '005930', '091810', '294870', '298020']  # List of ticker symbols
    weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])  # Corresponding weights (must sum to 1)

    analyze_portfolio(stocks, weights)