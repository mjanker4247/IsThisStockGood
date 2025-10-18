#!/usr/bin/env python3
"""
Example usage of the refactored Magic Formula analysis.

This script demonstrates how to use the modular functions
for stock analysis using Greenblatt's Magic Formula.
"""

import magic_formula

def main():
    """Run example analysis with different stock sets."""
    
    print("=" * 60)
    print("MAGIC FORMULA ANALYSIS - EXAMPLE USAGE")
    print("=" * 60)
    
    # Example 1: Analyze a small subset of tech stocks
    print("\n1. Analyzing Tech Stocks (AAPL, MSFT, GOOGL)")
    print("-" * 50)
    tech_stocks = ['AAPL', 'MSFT', 'GOOGL']
    tech_results = magic_formula.run_magic_formula_analysis(tech_stocks)
    
    # Example 2: Analyze individual functions
    print("\n2. Using Individual Functions")
    print("-" * 50)
    
    # Fetch data for a single stock
    print("Fetching data for Apple (AAPL)...")
    apple_data = magic_formula.fetch_financial_data(['AAPL'])
    
    # Create DataFrame
    df = magic_formula.create_financial_dataframe(apple_data)
    print(f"Financial data shape: {df.shape}")
    print(f"Available columns: {list(df.columns)}")
    
    # Calculate metrics
    metrics = magic_formula.calculate_magic_formula_metrics(df)
    print(f"Calculated metrics for AAPL:")
    print(f"  Earning Yield: {metrics.loc['AAPL', 'EarningYield']:.4f}")
    print(f"  ROC: {metrics.loc['AAPL', 'ROC']:.4f}")
    print(f"  Dividend Yield: {metrics.loc['AAPL', 'DividendYield']:.2f}%")
    
    # Example 3: Custom analysis
    print("\n3. Custom Analysis - Top 5 Value Stocks")
    print("-" * 50)
    
    # Use a subset of DOW stocks for faster analysis
    dow_subset = ['AAPL', 'MSFT', 'JNJ', 'PG', 'KO', 'WMT', 'MCD', 'DIS']
    custom_results = magic_formula.run_magic_formula_analysis(dow_subset)
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print("Note: This is for educational purposes only.")
    print("Always do your own research before making investment decisions!")

if __name__ == "__main__":
    main()
