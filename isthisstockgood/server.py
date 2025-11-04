import logging
from datetime import date
from flask import Flask, request, render_template, json
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_caching import Cache
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

# Configure caching
    app.config['CACHE_TYPE'] = 'simple'  # Use 'redis' for production
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    cache = Cache(app)
    
    # Configure rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"  # Use redis:// for production
    )
    
    # Create cached version of fetch function
    cached_fetch = create_cache_decorator(cache)(timeout=300)(fetchDataForTickerSymbol)

    # NEW: trust Traefik and honor X-Forwarded-Prefix -> SCRIPT_NAME=/stocks
    app.wsgi_app = ProxyFix(app.wsgi_app, x_prefix=1)
    
    @app.route('/api/ticker/nvda')
    @limiter.limit("30 per minute")
    def api_ticker():
      template_values = cached_fetch("NVDA")

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
      template_values = cached_fetch(ticker)
      if not template_values:
        return render_template('json/error.json', **{'error' : 'Invalid ticker symbol'})
      return render_template('json/stock_data.json', **template_values)

    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring."""
        return {'status': 'healthy', 'timestamp': str(date.today())}, 200
    
    @app.route('/cache/clear')
    @limiter.limit("5 per hour")
    def clear_cache():
        """Clear cache endpoint (admin use)."""
        cache.clear()
        return {'status': 'cache cleared'}, 200
    
    return app