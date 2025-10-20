
const APP_I18N = window.APP_I18N || {};
const TRANSLATIONS = APP_I18N.translations || {};
const LOCALE = APP_I18N.locale || 'en-US';
const BASE_PAGE_TITLE = APP_I18N.baseTitle || document.title;

const groupingFormatter = new Intl.NumberFormat(LOCALE, { useGrouping: true, maximumFractionDigits: 3 });
const integerFormatter = new Intl.NumberFormat(LOCALE, { useGrouping: true, maximumFractionDigits: 0 });
const decimalFormatter = new Intl.NumberFormat(LOCALE, {
  useGrouping: true,
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const TICKER_PATTERN = /^[A-Za-z]{1,5}(?:[.-][A-Za-z]{1,3})?$/;
const CHART_LABELS = TRANSLATIONS.chart_labels || ['1 Year', '3 Year', '5 Year', 'Max'];
const DATASET_LABELS = TRANSLATIONS.chart_dataset_labels || {};
const SUMMARY_METRIC_LABELS = TRANSLATIONS.summary_metric_labels || {};
const SUMMARY_ONE_YEAR_SUFFIX = TRANSLATIONS.summary_one_year_suffix || ' (1Y)';
const ERROR_MESSAGES = TRANSLATIONS.errors || {};
const LOADING_TEXT = TRANSLATIONS.loading || 'Loading';
const ANALYZING_TEMPLATE = TRANSLATIONS.analyzing || 'Analyzing {ticker}';
const SUMMARY_PROMPT_TEXT = TRANSLATIONS.summary_prompt || 'Financial trend data will appear here after a successful search.';
const SUMMARY_UNAVAILABLE_TEXT = TRANSLATIONS.summary_unavailable || 'Financial trend data is unavailable for this company.';
const SUMMARY_PREFIX = TRANSLATIONS.summary_prefix || '1-year growth snapshot:';
const NEGATIVE_CASH_FLOW_TEXT = TRANSLATIONS.negative_cash_flow || 'Negative Cash Flow';
const UNDEFINED_TEXT = TRANSLATIONS.undefined || 'Undefined';
const TOOLTIP_NO_DATA = TRANSLATIONS.chart_tooltip_no_data || 'No data';
const AXIS_TITLE = TRANSLATIONS.chart_axis || 'Growth (%)';
const NOT_AVAILABLE_TEXT = TRANSLATIONS.not_available || 'N/A';

let financialTrendChart = null;

class Color {

  static green() {
    return '#C3E6CB';
  }

  static orange() {
    return '#FFD8A8';
  }

  static red() {
    return '#ffbdc4';
  }

  static white() {
    return '#FFFFFF';
  }

  static yellow() {
    return '#FFF0B5';
  }
}

function formatTemplate(template, replacements) {
  if (typeof template !== 'string') {
    return '';
  }
  return template.replace(/\{(\w+)\}/g, (match, key) => {
    if (Object.prototype.hasOwnProperty.call(replacements, key)) {
      const value = replacements[key];
      return value === undefined || value === null ? '' : String(value);
    }
    return match;
  });
}

function getNumericValue(selector) {
  const $element = $(selector);
  if (!$element.length) {
    return Number.NaN;
  }
  const numericValue = $element.data('numeric-value');
  return typeof numericValue === 'number' && !Number.isNaN(numericValue) ? numericValue : Number.NaN;
}

function clearNumericValue(selector) {
  const $element = $(selector);
  $element.removeData('numeric-value');
}

$(document).ready(function() {
  const loader = document.querySelector('popup-loading');
  const $form = $('#searchboxform');
  const $tickerInput = $('#ticker');
  const $errorContainer = $('#ticker-error');
  const $analyzeButton = $('#analyze-button');
  const $analyzeSpinner = $('#analyze-spinner');

  initializeFinancialTrendChart();

  $tickerInput.on('input', function() {
    const sanitizedValue = sanitizeTickerInput($(this).val());
    if (sanitizedValue !== $(this).val()) {
      $(this).val(sanitizedValue);
    }
    clearTickerError();
  });

  $tickerInput.on('blur', function() {
    $(this).val(sanitizeTickerInput($(this).val()));
  });

  $form.on('submit', function(event) {
    event.preventDefault();

    const ticker = sanitizeTickerInput($tickerInput.val());

    if (!ticker) {
      showTickerError(ERROR_MESSAGES.ticker_required || 'Ticker is required.');
      $tickerInput.focus();
      return;
    }

    if (!TICKER_PATTERN.test(ticker)) {
      showTickerError(ERROR_MESSAGES.ticker_invalid || 'Please enter a valid ticker (letters with optional dot or hyphen).');
      $tickerInput.focus();
      return;
    }

    $tickerInput.val(ticker);
    clearTickerError();

    const loadingMessage = formatTemplate(ANALYZING_TEMPLATE, { ticker }) || LOADING_TEXT;
    setLoadingState(true, loadingMessage);

    const request = $.post($form.attr('action'), { ticker: ticker });

    request.fail(function(response) {
      handleNetworkError(response);
      updateFinancialTrendSummary(null);
    });

    request.done(function(json_data) {
      try {
        const data = JSON.parse(json_data);
        if (data.error) {
          showTickerError(data.error);
          showSnackbar(data.error);
          updateFinancialTrendSummary(null);
          return;
        }

        updateWebsiteTitle(data);
        updateMeaningSection(data);
        updateMetricSections(data);
        updateFinancialTrendChartWithData(data);
        updateFinancialTrendSummary(data);
      } catch (error) {
        const message = ERROR_MESSAGES.response_unprocessable || 'We were unable to process the response. Please try again.';
        showTickerError(message);
        showSnackbar(message);
        updateFinancialTrendSummary(null);
      }
    });

    request.always(function() {
      setLoadingState(false);
    });
  });

  function setLoadingState(isLoading, message) {
    $analyzeButton.prop('disabled', isLoading);
    $analyzeButton.attr('aria-busy', isLoading);
    $analyzeSpinner.toggleClass('d-none', !isLoading);

    if (loader) {
      const loaderMessage = message || LOADING_TEXT;
      loader.setAttribute('data-message', loaderMessage);
      if (typeof loader.show === 'function' && typeof loader.hide === 'function') {
        if (isLoading) {
          loader.show();
        } else {
          loader.hide();
        }
      }
    }
  }

  function showTickerError(message) {
    $errorContainer.text(message);
    $tickerInput.attr('aria-invalid', 'true');
  }

  function clearTickerError() {
    $tickerInput.removeAttr('aria-invalid');
    if ($errorContainer.text()) {
      $errorContainer.text('');
    }
  }

  function showSnackbar(message) {
    $.snackbar({
      content: message,
      style: 'toast',
      timeout: 4500
    });
  }

  function handleNetworkError(response) {
    let message = ERROR_MESSAGES.unexpected || 'There was an unexpected error. Please try again.';
    if (response && response.status === 0) {
      message = ERROR_MESSAGES.network || 'Network connection lost. Check your internet connection and try again.';
    } else if (response && response.status) {
      const formatted = formatTemplate(ERROR_MESSAGES.status_code, { status: response.status });
      message = formatted || message;
    }
    showTickerError(message);
    showSnackbar(message);
  }

  function updateWebsiteTitle(data) {
    if (data.ticker) {
      document.title = `${BASE_PAGE_TITLE} - ${data.ticker.toUpperCase()}`;
    }
  }

  function updateMeaningSection(data) {
    if (data.description) {
      $('#meaning').html(data.description);
    }
  }

  function updateMetricSections(data) {
    updateBigFiveHtmlWithDataForKey(data, 'eps');
    updateBigFiveHtmlWithDataForKey(data, 'sales');
    updateBigFiveHtmlWithDataForKey(data, 'equity');
    updateBigFiveHtmlWithDataForKey(data, 'roic');
    updateBigFiveHtmlWithDataForKey(data, 'cash');

    updateHtmlWithValueForKey(data, 'debt_equity_ratio', true);
    colorCellWithIDForZeroBasedRange('#debt_equity_ratio', [1, 2, 3]);
    updateHtmlWithValueForKey(data, 'total_debt', true);
    updateHtmlWithValueForKey(data, 'free_cash_flow', true);

    const freeCashFlow = getNumericValue('#free_cash_flow');
    if (Number.isFinite(freeCashFlow) && freeCashFlow >= 0) {
      updateHtmlWithValueForKey(data, 'debt_payoff_time', false);
      colorCellWithIDForZeroBasedRange('#debt_payoff_time', [2, 3, 4]);
    } else {
      const $debtPayoffTime = $('#debt_payoff_time');
      $debtPayoffTime.html(NEGATIVE_CASH_FLOW_TEXT);
      clearNumericValue('#debt_payoff_time');
      colorCellWithBackgroundColor('#debt_payoff_time', Color.red());
    }

    updateHtmlWithValueForKey(data, 'margin_of_safety_price', false);
    updateHtmlWithValueForKey(data, 'current_price', false);
    updateHtmlWithValueForKey(data, 'sticker_price', false);
    const marginOfSafety = data['margin_of_safety_price'];
    if (marginOfSafety || marginOfSafety === 0) {
      const range = [marginOfSafety, marginOfSafety * 1.25, marginOfSafety * 1.5];
      colorCellWithIDForZeroBasedRange('#current_price', range);
    } else {
      colorCellWithBackgroundColor('#current_price', Color.red());
    }

    let key = 'payback_time';
    updateHtmlWithValueForKey(data, key, true);
    colorCellWithIDForZeroBasedRange('#' + key, [6, 8, 10]);
    if (!data[key] && data[key] !== 0) {
      colorCellWithBackgroundColor('#' + key, Color.red());
    }

    const tenCapKey = 'ten_cap_price';
    const tenCapSelector = '#' + tenCapKey;
    const currentPrice = data['current_price'];
    updateHtmlWithValueForKey(data, tenCapKey, false);
    if (!data[tenCapKey] && data[tenCapKey] !== 0) {
      colorCellWithBackgroundColor(tenCapSelector, Color.red());
    } else if (currentPrice > data[tenCapKey]) {
      colorCellWithBackgroundColor(tenCapSelector, Color.red());
    } else {
      colorCellWithBackgroundColor(tenCapSelector, Color.green());
    }

    updateHtmlWithValueForKey(data, 'average_volume', true);
    const averageVolume = Number(data['average_volume']);
    const currentPriceValue = Number(currentPrice);
    const minVolume = currentPriceValue <= 1.0 ? 1000000 : 500000;
    const averageVolumeColor = Number.isFinite(averageVolume) && averageVolume >= minVolume ? Color.green() : Color.red();
    colorCellWithBackgroundColor('#average_volume', averageVolumeColor);
    const sharesToHold = Number.isFinite(averageVolume)
      ? integerFormatter.format(Math.round(averageVolume * 0.01))
      : NOT_AVAILABLE_TEXT;
    $('#shares_to_hold').html(sharesToHold);
  }
});

function initializeFinancialTrendChart() {
  const chartElement = document.getElementById('financial-trend-chart');
  if (!chartElement || typeof Chart === 'undefined') {
    return;
  }

  const datasets = [
    { metricKey: 'eps', label: DATASET_LABELS.eps || 'EPS Growth', borderColor: '#007bff', backgroundColor: 'rgba(0, 123, 255, 0.15)' },
    { metricKey: 'sales', label: DATASET_LABELS.sales || 'Sales Growth', borderColor: '#17a2b8', backgroundColor: 'rgba(23, 162, 184, 0.15)' },
    { metricKey: 'equity', label: DATASET_LABELS.equity || 'Equity Growth', borderColor: '#28a745', backgroundColor: 'rgba(40, 167, 69, 0.15)' },
    { metricKey: 'cash', label: DATASET_LABELS.cash || 'Cash Flow Growth', borderColor: '#ff9800', backgroundColor: 'rgba(255, 152, 0, 0.15)' },
    { metricKey: 'roic', label: DATASET_LABELS.roic || 'ROIC', borderColor: '#9c27b0', backgroundColor: 'rgba(156, 39, 176, 0.15)' }
  ];

  const formattedDatasets = datasets.map(dataset => ({
    label: dataset.label,
    data: Array(CHART_LABELS.length).fill(null),
    borderColor: dataset.borderColor,
    backgroundColor: dataset.backgroundColor,
    tension: 0.35,
    spanGaps: true,
    fill: true,
    pointRadius: 4,
    pointHoverRadius: 6,
    metricKey: dataset.metricKey
  }));

  financialTrendChart = new Chart(chartElement.getContext('2d'), {
    type: 'line',
    data: {
      labels: CHART_LABELS,
      datasets: formattedDatasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          ticks: {
            callback: function(value) {
              return `${value}%`;
            }
          },
          title: {
            display: true,
            text: AXIS_TITLE
          }
        }
      },
      plugins: {
        legend: {
          labels: {
            usePointStyle: true
          }
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              let label = context.dataset.label || '';
              if (label) {
                label += ': ';
              }
              if (context.parsed.y !== null && !Number.isNaN(context.parsed.y)) {
                label += `${context.parsed.y}%`;
              } else {
                label += TOOLTIP_NO_DATA;
              }
              return label;
            }
          }
        }
      }
    }
  });
}

function updateFinancialTrendChartWithData(data) {
  if (!financialTrendChart) {
    return;
  }

  financialTrendChart.data.labels = CHART_LABELS;
  financialTrendChart.data.datasets.forEach(dataset => {
    const metricValues = Array.isArray(data[dataset.metricKey]) ? data[dataset.metricKey] : [];
    dataset.data = CHART_LABELS.map((_, index) => {
      const value = metricValues[index];
      const numericValue = Number(value);
      if (Number.isFinite(numericValue)) {
        return Number(numericValue.toFixed(2));
      }
      return null;
    });
    dataset.label = DATASET_LABELS[dataset.metricKey] || dataset.label;
  });
  financialTrendChart.options.scales.y.title.text = AXIS_TITLE;
  financialTrendChart.update();
}

function updateFinancialTrendSummary(data) {
  const $summary = $('#financial-trend-summary');
  if (!$summary.length) {
    return;
  }

  if (!data) {
    $summary.text(SUMMARY_PROMPT_TEXT);
    return;
  }

  const metricKeys = ['eps', 'sales', 'equity', 'cash', 'roic'];
  const highlights = metricKeys.map(key => {
    const metricValues = Array.isArray(data[key]) ? data[key] : [];
    const oneYearValue = Number(metricValues[0]);
    if (!Number.isFinite(oneYearValue)) {
      return null;
    }
    const metricLabel = SUMMARY_METRIC_LABELS[key] || key.toUpperCase();
    const formattedValue = decimalFormatter.format(oneYearValue);
    return `${metricLabel} ${formattedValue}%${SUMMARY_ONE_YEAR_SUFFIX}`;
  }).filter(Boolean);

  if (!highlights.length) {
    $summary.text(SUMMARY_UNAVAILABLE_TEXT);
    return;
  }

  const summaryText = `${SUMMARY_PREFIX} ${highlights.slice(0, 3).join(', ')}.`;
  $summary.text(summaryText);
}

function sanitizeTickerInput(value) {
  if (!value) {
    return '';
  }
  return value.toUpperCase().replace(/[^A-Z.-]/g, '').slice(0, 8);
}

function updateHtmlWithValueForKey(data, key, useGrouping) {
  const $element = $('#' + key);
  if (!$element.length) {
    return;
  }

  const rawValue = data[key];
  const numericValue = Number(rawValue);

  if (rawValue === null || rawValue === undefined || Number.isNaN(numericValue)) {
    $element.html(UNDEFINED_TEXT);
    clearNumericValue('#' + key);
    return;
  }

  const formatter = useGrouping ? groupingFormatter : decimalFormatter;
  const formattedValue = formatter.format(numericValue);
  $element.html(formattedValue);
  $element.data('numeric-value', numericValue);
}

function updateBigFiveHtmlWithDataForKey(data, key) {
  let row_data = data[key];
  let suffixes = ['_1_val', '_3_val', '_5_val', '_max_val'];
  for (let i = 0; i < suffixes.length; i++) {
    let element_id = '#' + key + suffixes[i];
    let displayValue = '-';
    const numericValue = Array.isArray(row_data) && i < row_data.length ? Number(row_data[i]) : Number.NaN;
    if (Number.isFinite(numericValue)) {
      displayValue = decimalFormatter.format(numericValue);
      $(element_id).data('numeric-value', numericValue);
    } else {
      if (Array.isArray(row_data) && i < row_data.length && row_data[i] !== null && row_data[i] !== undefined) {
        displayValue = row_data[i];
      }
      $(element_id).removeData('numeric-value');
    }
    $(element_id).html(displayValue);

    if (!Number.isFinite(numericValue)) {
      const color = (i === 0) ? Color.red() : Color.white();
      colorCellWithBackgroundColor(element_id, color);
    } else {
      colorCellWithIDForRange(element_id, [0, 5, 10]);
    }
  }
}

function colorCellWithBackgroundColor(id, backgroundColor) {
    $(id).css('background-color', backgroundColor);
}

function colorCellWithIDForRange(id, range) {
    if (range.length !== 3) {
      return;
    }
    const value = getNumericValue(id);
    if (!Number.isFinite(value)) {
      colorCellWithBackgroundColor(id, Color.white());
      return;
    }
    let backgroundColor = Color.red();
    if (value >= range[2]) {
      backgroundColor = Color.green();
    } else if (value >= range[1]) {
      backgroundColor = Color.yellow();
    } else if (value >= range[0]) {
      backgroundColor = Color.orange();
    }
    colorCellWithBackgroundColor(id, backgroundColor);
}

function colorCellWithIDForZeroBasedRange(id, range) {
    if (range.length !== 3) {
      return;
    }
    const value = getNumericValue(id);
    if (!Number.isFinite(value)) {
      colorCellWithBackgroundColor(id, Color.white());
      return;
    }

    let backgroundColor = Color.green();
    if (value >= range[2]) {
      backgroundColor = Color.red();
    } else if (value >= range[1]) {
      backgroundColor = Color.orange();
    } else if (value >= range[0]) {
      backgroundColor = Color.yellow();
    }

    colorCellWithBackgroundColor(id, backgroundColor);
}
