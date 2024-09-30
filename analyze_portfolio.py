import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt

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

def analyze_portfolio():
    # Define your portfolio
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN']  # List of ticker symbols
    weights = np.array([0.25, 0.25, 0.25, 0.25])  # Corresponding weights (must sum to 1)

    # Fetch historical adjusted closing prices
    data = fetch_data(stocks, start_date='2020-01-01', end_date='2023-10-01')

    # Calculate daily returns
    returns = data.pct_change().dropna()

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

    # Display the results
    print(f"Portfolio Expected Annual Return: {portfolio_return:.2%}")
    print(f"Portfolio Annual Volatility: {portfolio_volatility:.2%}")
    print(f"Portfolio Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Portfolio VaR (95% confidence): {VaR:.2%}")
    print(f"Portfolio Expected Shortfall (ES): {ES:.2%}")

if __name__ == "__main__":
    analyze_portfolio()

    '''
    Variance, Standard Deviation:
        measure of how much returns of the assets in portfolio deviate from the the average. 
            Higher variance -> higher potential fluctuations 
            lower variance -> stability

    Beta:
        portfolio's sensitivity to the market movement. 
            Beta  = 1 : moves with the market
            Beta  > 1 : moves faster than the market
            Beta < 1 : moves slower than the market
            Beta = 0 : independent from the market
            Beta  < 0 : moves opposite direction from the market. 

    Sharpe:
        risk-adjusted return of portfolio.
        measures performance of investment compared to risk-free assets such as bond.

        std deviation is high -> lower return per risk
        higher return -> higher return per risk
        higher risk-free rate -> lower return per risk

        greater than 1.0 -> acceptable
        greater than 2.0 -> good
        greater than 3.0 -> excellent
        lower than 1.0 - > suboptimal (not the best)
        
'''