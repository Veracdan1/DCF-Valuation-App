# DCF Valuation Application

## Project Description
This project is a corporate valuation tool that estimates the intrinsic value of publicly traded companies using a Discounted Cash Flow (DCF) model. The application accepts a stock ticker, retrieves financial data automatically, and calculates enterprise value, equity value, and intrinsic value per share.

## Project Goals
The goal of this application is to allow analysts to test different valuation assumptions such as WACC, growth rate, and terminal growth rate instead of relying on a single static valuation.

## Tools Used
- Python
- Streamlit
- yfinance
- pandas
- numpy

## Data Sources
Financial data is retrieved using the yfinance library, which aggregates financial data from Yahoo Finance.

## Instructions to Run the Application
1. Install Python
2. Install required libraries:

pip install streamlit yfinance pandas numpy

3. Run the application:

streamlit run app.py

4. Enter a stock ticker such as AAPL or MSFT.

## AI Usage Disclosure
AI tools were used to assist with code generation and debugging. All financial logic and valuation outputs were reviewed and validated manually.
