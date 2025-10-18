import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import warnings
warnings.filterwarnings('ignore')

# We will pick the 30 stocks listed in DOW Jones index, feel free to change these as per your requirement.
DOW_STOCKS = ["AXP","AAPL","BA","CAT","CVX","CSCO","DIS","DOW", "XOM",
              "HD","IBM","INTC","JNJ","KO","MCD","MMM","MRK","MSFT",
              "NKE","PFE","PG","TRV","UTX","UNH","VZ","V","WMT","WBA"]


def fetch_financial_data(tickers: List[str]) -> Dict[str, Dict]:
    """
    Fetch financial data for given tickers using yfinance.
    
    Args:
        tickers: List of stock ticker symbols
        
    Returns:
        Dictionary containing financial data for each ticker
    """
    financial_data = {}
    
    for ticker in tickers:
        try:
            print(f"Fetching data for {ticker}...")
            stock = yf.Ticker(ticker)
            
            # Get financial statements
            info = stock.info
            financials = stock.financials
            balance_sheet = stock.balance_sheet
            cashflow = stock.cashflow
            
            # Extract key metrics with better error handling
            def safe_get_financial_data(data, key, default=np.nan):
                """Safely extract financial data with fallback"""
                try:
                    if key in data.index:
                        return data.loc[key].iloc[0] if not data.loc[key].empty else default
                    return default
                except:
                    return default
            
            ticker_data = {
                'MarketCap': info.get('marketCap', np.nan),
                'EBITDA': info.get('ebitda', np.nan),
                'NetIncome': safe_get_financial_data(financials, 'Net Income'),
                'TotalRevenue': safe_get_financial_data(financials, 'Total Revenue'),
                'OperatingCashFlow': safe_get_financial_data(cashflow, 'Total Cash From Operating Activities'),
                'CapitalExpenditure': abs(safe_get_financial_data(cashflow, 'Capital Expenditures', 0)),
                'TotalCurrentAssets': safe_get_financial_data(balance_sheet, 'Total Current Assets'),
                'TotalCurrentLiabilities': safe_get_financial_data(balance_sheet, 'Total Current Liabilities'),
                'NetPropertyPlantEquipment': safe_get_financial_data(balance_sheet, 'Property Plant Equipment'),
                'TotalStockholderEquity': safe_get_financial_data(balance_sheet, 'Total Stockholder Equity'),
                'LongTermDebt': safe_get_financial_data(balance_sheet, 'Long Term Debt'),
                'DividendYield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'DepreciationAmortization': safe_get_financial_data(financials, 'Depreciation')
            }
            
            financial_data[ticker] = ticker_data
            print(f"Data successfully fetched for {ticker}")
            
        except Exception as e:
            print(f"Problem fetching data for {ticker}: {str(e)}")
            financial_data[ticker] = {}
    
    return financial_data


def create_financial_dataframe(financial_data: Dict[str, Dict]) -> pd.DataFrame:
    """
    Create a cleaned DataFrame from financial data.
    
    Args:
        financial_data: Dictionary containing financial data for each ticker
        
    Returns:
        Cleaned DataFrame with financial metrics
    """
    # Convert to DataFrame
    df = pd.DataFrame(financial_data).T
    
    # Remove columns with all NaN values
    df = df.dropna(how='all', axis=1)
    
    # Convert all values to numeric, coercing errors to NaN
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove rows (tickers) with all NaN values
    df = df.dropna(how='all', axis=0)
    
    return df


def calculate_magic_formula_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate metrics required for the Magic Formula analysis.
    
    Args:
        df: DataFrame with financial data
        
    Returns:
        DataFrame with calculated metrics
    """
    # Create a copy for calculations
    metrics_df = df.copy()
    
    # Ensure all required columns exist with default values
    required_columns = {
        'MarketCap': 0,
        'EBITDA': 0,
        'DepreciationAmortization': 0,
        'LongTermDebt': 0,
        'TotalCurrentAssets': 0,
        'TotalCurrentLiabilities': 0,
        'OperatingCashFlow': 0,
        'CapitalExpenditure': 0,
        'NetPropertyPlantEquipment': 0,
        'TotalStockholderEquity': 0,
        'DividendYield': 0
    }
    
    for col, default_val in required_columns.items():
        if col not in metrics_df.columns:
            metrics_df[col] = default_val
        else:
            metrics_df[col] = metrics_df[col].fillna(default_val)
    
    # Calculate EBIT (Earnings Before Interest and Taxes)
    # EBIT = EBITDA - Depreciation & Amortization
    metrics_df['EBIT'] = metrics_df['EBITDA'] - metrics_df['DepreciationAmortization']
    
    # Calculate Total Enterprise Value (TEV)
    # TEV = Market Cap + Total Debt - (Current Assets - Current Liabilities)
    metrics_df['TEV'] = (metrics_df['MarketCap'] + 
                        metrics_df['LongTermDebt'] - 
                        (metrics_df['TotalCurrentAssets'] - 
                         metrics_df['TotalCurrentLiabilities']))
    
    # Calculate Earning Yield = EBIT / TEV (avoid division by zero)
    metrics_df['EarningYield'] = np.where(
        metrics_df['TEV'] != 0, 
        metrics_df['EBIT'] / metrics_df['TEV'], 
        0
    )
    
    # Calculate Free Cash Flow Yield = (Operating Cash Flow - Capital Expenditure) / Market Cap
    metrics_df['FCFYield'] = np.where(
        metrics_df['MarketCap'] != 0,
        ((metrics_df['OperatingCashFlow'] - 
          metrics_df['CapitalExpenditure']) / 
         metrics_df['MarketCap']),
        0
    )
    
    # Calculate Return on Capital (ROC) = EBIT / (PPE + Current Assets - Current Liabilities)
    capital_base = (metrics_df['NetPropertyPlantEquipment'] + 
                   metrics_df['TotalCurrentAssets'] - 
                   metrics_df['TotalCurrentLiabilities'])
    
    metrics_df['ROC'] = np.where(
        capital_base != 0,
        metrics_df['EBIT'] / capital_base,
        0
    )
    
    # Calculate Book to Market ratio = Book Value / Market Cap
    metrics_df['BookToMkt'] = np.where(
        metrics_df['MarketCap'] != 0,
        metrics_df['TotalStockholderEquity'] / metrics_df['MarketCap'],
        0
    )
    
    return metrics_df


def apply_magic_formula_ranking(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply Greenblatt's Magic Formula ranking based on Earning Yield and ROC.
    
    Args:
        metrics_df: DataFrame with calculated metrics
        
    Returns:
        DataFrame with Magic Formula rankings
    """
    ranking_df = metrics_df.copy()
    
    # Rank by Earning Yield (higher is better)
    ranking_df['EarningYieldRank'] = ranking_df['EarningYield'].rank(ascending=False, method='first')
    
    # Rank by ROC (higher is better)
    ranking_df['ROCRank'] = ranking_df['ROC'].rank(ascending=False, method='first')
    
    # Combined rank (lower is better)
    ranking_df['CombinedRank'] = ranking_df['EarningYieldRank'] + ranking_df['ROCRank']
    ranking_df['MagicFormulaRank'] = ranking_df['CombinedRank'].rank(method='first')
    
    return ranking_df


def get_top_value_stocks(ranking_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Get top value stocks based on Magic Formula ranking.
    
    Args:
        ranking_df: DataFrame with Magic Formula rankings
        top_n: Number of top stocks to return
        
    Returns:
        DataFrame with top value stocks
    """
    top_stocks = (ranking_df.sort_values('MagicFormulaRank')
                 .head(top_n)[['EarningYield', 'ROC', 'DividendYield', 'MagicFormulaRank']]
                 .fillna(0))
    
    return top_stocks


def get_high_dividend_stocks(metrics_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Get stocks with highest dividend yields.
    
    Args:
        metrics_df: DataFrame with calculated metrics
        top_n: Number of top dividend stocks to return
        
    Returns:
        DataFrame with high dividend stocks
    """
    high_div_stocks = (metrics_df.sort_values('DividendYield', ascending=False)
                      .head(top_n)[['DividendYield']]
                      .fillna(0))
    
    return high_div_stocks


def get_combined_ranking(metrics_df: pd.DataFrame) -> pd.DataFrame:
    """
    Get combined ranking including Magic Formula and Dividend Yield.
    
    Args:
        metrics_df: DataFrame with calculated metrics
        
    Returns:
        DataFrame with combined rankings
    """
    combined_df = metrics_df.copy()
    
    # Rank by Earning Yield
    combined_df['EarningYieldRank'] = combined_df['EarningYield'].rank(ascending=False, method='first')
    
    # Rank by ROC
    combined_df['ROCRank'] = combined_df['ROC'].rank(ascending=False, method='first')
    
    # Rank by Dividend Yield
    combined_df['DividendYieldRank'] = combined_df['DividendYield'].rank(ascending=False, method='first')
    
    # Combined rank (lower is better)
    combined_df['CombinedRank'] = (combined_df['EarningYieldRank'] + 
                                  combined_df['ROCRank'] + 
                                  combined_df['DividendYieldRank'])
    combined_df['FinalRank'] = combined_df['CombinedRank'].rank(method='first')
    
    return combined_df


def run_magic_formula_analysis(tickers: List[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Run the complete Magic Formula analysis.
    
    Args:
        tickers: List of stock tickers to analyze. If None, uses DOW_STOCKS
        
    Returns:
        Dictionary containing analysis results
    """
    if tickers is None:
        tickers = DOW_STOCKS
    
    print("Starting Magic Formula Analysis...")
    print("=" * 50)
    
    # Step 1: Fetch financial data
    print("Step 1: Fetching financial data...")
    financial_data = fetch_financial_data(tickers)
    
    # Step 2: Create cleaned DataFrame
    print("\nStep 2: Processing financial data...")
    df = create_financial_dataframe(financial_data)
    
    # Step 3: Calculate Magic Formula metrics
    print("Step 3: Calculating Magic Formula metrics...")
    metrics_df = calculate_magic_formula_metrics(df)
    
    # Step 4: Apply Magic Formula ranking
    print("Step 4: Applying Magic Formula ranking...")
    ranking_df = apply_magic_formula_ranking(metrics_df)
    
    # Step 5: Get results
    print("Step 5: Generating analysis results...")
    
    # Top value stocks
    top_value_stocks = get_top_value_stocks(ranking_df)
    print("\n" + "=" * 50)
    print("TOP VALUE STOCKS (Magic Formula)")
    print("=" * 50)
    print(top_value_stocks)
    
    # High dividend stocks
    high_dividend_stocks = get_high_dividend_stocks(metrics_df)
    print("\n" + "=" * 50)
    print("HIGH DIVIDEND STOCKS")
    print("=" * 50)
    print(high_dividend_stocks)
    
    # Combined ranking
    combined_ranking = get_combined_ranking(metrics_df)
    top_combined = (combined_ranking.sort_values('FinalRank')
                   .head(10)[['EarningYield', 'ROC', 'DividendYield', 'FinalRank']]
                   .fillna(0))
    
    print("\n" + "=" * 50)
    print("COMBINED RANKING (Magic Formula + Dividend Yield)")
    print("=" * 50)
    print(top_combined)
    
    return {
        'financial_data': df,
        'metrics': metrics_df,
        'magic_formula_ranking': ranking_df,
        'top_value_stocks': top_value_stocks,
        'high_dividend_stocks': high_dividend_stocks,
        'combined_ranking': combined_ranking,
        'top_combined': top_combined
    }


if __name__ == "__main__":
    # Run the analysis
    results = run_magic_formula_analysis()
    
    print("\n" + "=" * 50)
    print("ANALYSIS COMPLETE")
    print("=" * 50)
    print("Note: Please do not use these results to make actual investments.")
    print("Do your own research and make decisions based on that. Happy investing! :)")


