import logging
from datetime import date
from flask import Flask, request, render_template, json
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps

def get_logger():
    logger = logging.getLogger("IsThisStockGood")
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    h_format = logging.Formatter('%(name)s - %(levelname)s : %(message)s')
    handler.setFormatter(h_format)
    logger.addHandler(handler)
    return logger


def create_cache_decorator(cache):
    """Create a caching decorator for ticker data."""
    def cache_ticker_data(timeout=300):
        def decorator(f):
            @wraps(f)
            def decorated_function(ticker):
                cache_key = f'ticker_data_{ticker.upper()}'
                result = cache.get(cache_key)
                if result is not None:
                    return result
                result = f(ticker)
                if result:
                    cache.set(cache_key, result, timeout=timeout)
                return result
            return decorated_function
        return decorator
    return cache_ticker_data

def create_app(fetchDataForTickerSymbol):
    app = Flask(__name__)

    # Import cache functions
    from isthisstockgood.DataFetcher import clear_cache, get_cache_stats
    
    # Configure rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"  # Use redis:// for production
    )

    # NEW: trust Traefik and honor X-Forwarded-Prefix -> SCRIPT_NAME=/stocks
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)
    
    @app.route('/api/ticker/nvda')
    @limiter.limit("30 per minute")
    def api_ticker():
      template_values = fetchDataForTickerSymbol("NVDA")

      if not template_values:
        data = render_template('json/error.json', **{'error' : 'Invalid ticker symbol'})
      else:
        data = render_template('json/stock_data.json', **template_values)

      return app.response_class(
        response=data,
        status=200,
        mimetype='application/json'
    )

    @app.route('/api')
    def api():
      data = {}
      return app.response_class(
        response=json.dumps(data),
        status=200,
        mimetype='application/json'
    )


    @app.route('/')
    def homepage():
      if request.environ['HTTP_HOST'].endswith('.appspot.com'):  #Redirect the appspot url to the custom url
        return '<meta http-equiv="refresh" content="0; url=https://isthisstockgood.com" />'

      template_values = {
        'page_title' : "Is This Stock Good?",
        'current_year' : date.today().year,
      }
      return render_template('home.html', **template_values)


    @app.route('/search', methods=['POST'])
    @limiter.limit("10 per minute")
    def search():
      if request.environ['HTTP_HOST'].endswith('.appspot.com'):  #Redirect the appspot url to the custom url
        return '<meta http-equiv="refresh" content="0; url=http://isthisstockgood.com" />'

      ticker = request.values.get('ticker')
      template_values = fetchDataForTickerSymbol(ticker)
      if not template_values:
        return render_template('json/error.json', **{'error' : 'Invalid ticker symbol'})
      return render_template('json/stock_data.json', **template_values)

    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        cache_stats = get_cache_stats()
        return {
            'status': 'healthy',
            'timestamp': str(date.today()),
            'cache': 'in-memory',
            'cache_size': cache_stats.get('size', 0)
        }, 200
    
    @app.route('/cache/clear')
    @limiter.limit("5 per hour")
    def clear_cache_route():
        """Clear cache endpoint (admin use)."""
        clear_cache()
        return {'status': 'cache cleared'}, 200
    
    @app.route('/cache/stats')
    @limiter.limit("30 per minute")
    def cache_stats():
        """Cache statistics endpoint."""
        stats = get_cache_stats()
        return stats, 200
      
      
    return app