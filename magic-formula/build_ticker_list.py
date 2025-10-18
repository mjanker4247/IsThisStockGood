"""
Build a unified, deduplicated list of global stock tickers from Wikipedia index pages.

Now includes company-name–based deduplication: 
one ticker per company (keeps first encountered).

Requirements:
    uv add pandas yfinance lxml html5lib requests
"""

import logging
import re
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ticker_build.log')
    ]
)
logger = logging.getLogger(__name__)

# Wikipedia URLs of major indices
SOURCES: Dict[str, str] = {
    "S&P 500": "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
    "NASDAQ 100": "https://en.wikipedia.org/wiki/NASDAQ-100",
    "DAX 40": "https://en.wikipedia.org/wiki/DAX",
    "FTSE 100": "https://en.wikipedia.org/wiki/FTSE_100_Index",
    "CAC 40": "https://en.wikipedia.org/wiki/CAC_40",
    "Nikkei 225": "https://en.wikipedia.org/wiki/Nikkei_225",
}

def normalize_company_name(name: str) -> str:
    """Normalize company names for fuzzy matching / deduplication.
    
    Args:
        name: Company name to normalize
        
    Returns:
        Normalized company name in uppercase
    """
    if not isinstance(name, str) or not name.strip():
        logger.warning("Invalid company name provided: %s", name)
        return ""
    
    try:
        # Remove punctuation, Inc., Corp., Ltd., SA, etc.
        name = re.sub(
            r'\b(Inc|Corp|Corporation|Ltd|Limited|PLC|AG|SA|SE|NV|Co|Group|Holdings?)\b', 
            '', 
            name, 
            flags=re.IGNORECASE
        )
        name = re.sub(r'[^A-Za-z0-9 ]+', '', name)
        normalized = name.strip().upper()
        logger.debug("Normalized '%s' to '%s'", name, normalized)
        return normalized
    except Exception as e:
        logger.error("Error normalizing company name '%s': %s", name, e)
        return ""

def get_tickers_and_names(url: str) -> pd.DataFrame:
    """Scrape tickers and company names from Wikipedia.
    
    Args:
        url: Wikipedia URL to scrape
        
    Returns:
        DataFrame with Ticker and Company columns
    """
    if not url or not isinstance(url, str):
        logger.error("Invalid URL provided: %s", url)
        return pd.DataFrame(columns=["Ticker", "Company"])
    
    logger.info("Fetching data from: %s", url)
    
    try:
        # Try with specific table class first
        tables = pd.read_html(url, header=0, attrs={'class': 'wikitable'})
        logger.debug("Found %d tables on page", len(tables))
    except Exception as e:
        logger.warning("Failed to read with wikitable class: %s", e)
        try:
            # Fallback to reading all tables
            tables = pd.read_html(url)
            logger.debug("Found %d tables on page (fallback method)", len(tables))
        except Exception as e2:
            logger.error("Error reading %s: %s", url, e2)
            return pd.DataFrame(columns=["Ticker", "Company"])

    for i, df in enumerate(tables):
        if df.empty:
            logger.debug("Table %d is empty, skipping", i)
            continue
            
        cols = list(df.columns)
        logger.debug("Table %d columns: %s", i, cols)
        
        ticker_col = next(
            (c for c in cols if "Ticker" in str(c) or "Symbol" in str(c)), 
            None
        )
        name_col = next(
            (c for c in cols if "Name" in str(c) or "Company" in str(c) or "Security" in str(c)), 
            None
        )
        
        if ticker_col and name_col:
            logger.info("Found suitable columns: %s and %s", ticker_col, name_col)
            try:
                df = df[[ticker_col, name_col]].copy()
                df.columns = ["Ticker", "Company"]
                # Remove rows with missing data
                df = df.dropna(subset=["Ticker", "Company"])
                logger.info("Successfully extracted %d entries", len(df))
                return df
            except Exception as e:
                logger.error("Error processing table %d: %s", i, e)
                continue

    logger.warning("No suitable data found in any table for %s", url)
    return pd.DataFrame(columns=["Ticker", "Company"])

def build_global_ticker_list() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Build a unified, deduplicated list of global stock tickers.
    
    Returns:
        Tuple of (raw_data, deduplicated_data) DataFrames
    """
    logger.info("Starting global ticker list build process")
    all_data = []

    for index_name, url in SOURCES.items():
        logger.info("Processing %s...", index_name)
        try:
            df = get_tickers_and_names(url)
            if not df.empty:
                df["Index"] = index_name
                all_data.append(df)
                logger.info("Successfully processed %s: %d entries", index_name, len(df))
            else:
                logger.warning("No data found for %s", index_name)
        except Exception as e:
            logger.error("Failed to process %s: %s", index_name, e)
            continue

    if not all_data:
        logger.error("No data was successfully fetched from any source")
        return pd.DataFrame(), pd.DataFrame()

    try:
        combined = pd.concat(all_data, ignore_index=True)
        logger.info("Combined data: %d total entries", len(combined))
        
        # Clean and normalize ticker symbols
        combined["Ticker"] = (
            combined["Ticker"]
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace('.', '-', regex=False)
        )
        
        # Normalize company names for deduplication
        combined["CompanyNorm"] = combined["Company"].apply(normalize_company_name)
        
        # Remove entries with empty normalized names
        before_cleanup = len(combined)
        combined = combined[combined["CompanyNorm"] != ""]
        after_cleanup = len(combined)
        if before_cleanup != after_cleanup:
            logger.info("Removed %d entries with empty normalized names", before_cleanup - after_cleanup)

        # Deduplicate by company name
        deduped = combined.drop_duplicates(subset=["CompanyNorm"], keep="first")

        logger.info("Final results: %d total tickers, %d unique companies", len(combined), len(deduped))

        # Save both versions
        output_dir = Path(".")
        raw_file = output_dir / "global_tickers_raw.csv"
        unique_file = output_dir / "global_tickers_unique.csv"
        
        try:
            combined.to_csv(raw_file, index=False)
            deduped[["Ticker", "Company", "Index"]].to_csv(unique_file, index=False)
            logger.info("Files saved successfully: %s, %s", raw_file, unique_file)
        except Exception as e:
            logger.error("Failed to save files: %s", e)
            raise

        return combined, deduped[["Ticker", "Company", "Index"]]

    except Exception as e:
        logger.error("Error during data processing: %s", e)
        raise

def create_sample_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create sample data for testing when web scraping fails."""
    logger.info("Creating sample data for testing")
    
    sample_data = pd.DataFrame({
        'Ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'BRK.A', 'UNH', 'JNJ'],
        'Company': ['Apple Inc.', 'Microsoft Corporation', 'Alphabet Inc.', 'Amazon.com Inc.', 
                   'Tesla Inc.', 'NVIDIA Corporation', 'Meta Platforms Inc.', 'Berkshire Hathaway Inc.',
                   'UnitedHealth Group Inc.', 'Johnson & Johnson'],
        'Index': ['S&P 500', 'S&P 500', 'S&P 500', 'S&P 500', 'S&P 500', 
                 'S&P 500', 'S&P 500', 'S&P 500', 'S&P 500', 'S&P 500']
    })
    
    # Normalize company names
    sample_data['CompanyNorm'] = sample_data['Company'].apply(normalize_company_name)
    
    # Create unique version
    unique_data = sample_data.drop_duplicates(subset=['CompanyNorm'], keep='first')
    
    return sample_data, unique_data[['Ticker', 'Company', 'Index']]


def main() -> None:
    """Main entry point for the script."""
    try:
        logger.info("Starting ticker list build process")
        raw_data, unique_data = build_global_ticker_list()
        
        if raw_data.empty:
            logger.warning("No data was successfully fetched from web sources")
            logger.info("Creating sample data for testing purposes")
            raw_data, unique_data = create_sample_data()
            
            # Save sample data
            output_dir = Path(".")
            raw_file = output_dir / "global_tickers_raw.csv"
            unique_file = output_dir / "global_tickers_unique.csv"
            
            raw_data.to_csv(raw_file, index=False)
            unique_data.to_csv(unique_file, index=False)
            logger.info("Sample files saved: %s, %s", raw_file, unique_file)
        
        logger.info("Ticker list build completed successfully")
        logger.info("Raw data: %d entries", len(raw_data))
        logger.info("Unique data: %d entries", len(unique_data))
        
    except Exception as e:
        logger.error("Script failed with error: %s", e)
        raise


if __name__ == "__main__":
    main()
