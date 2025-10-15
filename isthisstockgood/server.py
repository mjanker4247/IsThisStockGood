import logging
import os
from datetime import date
from flask import Flask, request, render_template, json, redirect


def get_logger():
    logger = logging.getLogger("IsThisStockGood")

    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)

    h_format = logging.Formatter('%(name)s - %(levelname)s : %(message)s')
    handler.setFormatter(h_format)

    logger.addHandler(handler)

    return logger

def _as_bool(value, default=False):
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def create_app(fetchDataForTickerSymbol):
    app = Flask(__name__)

    app.config.setdefault("ISG_REDIRECT_URL", os.environ.get("ISG_REDIRECT_URL", "https://isthisstockgood.com"))
    app.config.setdefault("ISG_REDIRECT_HOST_SUFFIX", os.environ.get("ISG_REDIRECT_HOST_SUFFIX", ".appspot.com"))
    app.config.setdefault(
        "ISG_ENABLE_REDIRECT",
        _as_bool(os.environ.get("ISG_ENABLE_REDIRECT"), default=True),
    )

    def maybe_redirect():
        redirect_url = app.config.get("ISG_REDIRECT_URL")
        redirect_suffix = app.config.get("ISG_REDIRECT_HOST_SUFFIX")
        redirect_enabled = app.config.get("ISG_ENABLE_REDIRECT", True)

        if redirect_enabled and redirect_url and redirect_suffix and request.host.endswith(redirect_suffix):
            return redirect(redirect_url, code=302)

        return None

    @app.route('/api/ticker/nvda')
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
      redirect_response = maybe_redirect()
      if redirect_response:
        return redirect_response

      template_values = {
        'page_title' : "Is This Stock Good?",
        'current_year' : date.today().year,
      }
      return render_template('home.html', **template_values)

    @app.route('/search', methods=['POST'])
    def search():
      redirect_response = maybe_redirect()
      if redirect_response:
        return redirect_response

      ticker = request.values.get('ticker')
      template_values = fetchDataForTickerSymbol(ticker)
      if not template_values:
        return render_template('json/error.json', **{'error' : 'Invalid ticker symbol'})
      return render_template('json/stock_data.json', **template_values)

    return app
