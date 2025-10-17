const TICKER_PATTERN = /^[A-Za-z]{1,5}(?:[-.][A-Za-z]{1,3})?$/;
const CHART_LABELS = ['1 Year', '3 Year', '5 Year', 'Max'];
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
      showTickerError('Ticker is required.');
      $tickerInput.focus();
      return;
    }

    if (!TICKER_PATTERN.test(ticker)) {
      showTickerError('Please enter a valid ticker (letters with optional dot or hyphen).');
      $tickerInput.focus();
      return;
    }

    $tickerInput.val(ticker);
    clearTickerError();

    setLoadingState(true, `Analyzing ${ticker}`);

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
        const message = 'We were unable to process the response. Please try again.';
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
      const loaderMessage = message || 'Loading';
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
    let message = 'There was an unexpected error. Please try again.';
    if (response && response.status === 0) {
      message = 'Network connection lost. Check your internet connection and try again.';
    } else if (response && response.status) {
      message = `There was an error (code ${response.status}). Please try again shortly.`;
    }
    showTickerError(message);
    showSnackbar(message);
  }

  function updateWebsiteTitle(data) {
    if (data.ticker) {
      let baseWebsiteTitle = document.title.split('?')[0] + '?';
      document.title = baseWebsiteTitle + ' - ' + data.ticker.toUpperCase();
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

    updateHtmlWithValueForKey(data, 'debt_equity_ratio', /*commas=*/true);
    colorCellWithIDForZeroBasedRange('#debt_equity_ratio', [1, 2, 3]);
    updateHtmlWithValueForKey(data, 'total_debt', /*commas=*/true);
    updateHtmlWithValueForKey(data, 'free_cash_flow', /*commas=*/true);
    let cash_flow = $('#free_cash_flow').html();
    if (parseInt(cash_flow.replace(/,/g, ''), 10) >= 0) {
      updateHtmlWithValueForKey(data, 'debt_payoff_time', /*commas=*/false);
      colorCellWithIDForZeroBasedRange('#debt_payoff_time', [2, 3, 4]);
    } else {
      $('#debt_payoff_time').html('Negative Cash Flow');
      $('#debt_payoff_time').css('background-color', Color.red());
    }

    updateHtmlWithValueForKey(data, 'margin_of_safety_price', /*commas=*/false);
    updateHtmlWithValueForKey(data, 'current_price', /*commas=*/false);
    updateHtmlWithValueForKey(data, 'sticker_price', /*commas=*/false);
    let marginOfSafety = data['margin_of_safety_price'];
    if (marginOfSafety || marginOfSafety === 0) {
      let range = [marginOfSafety, marginOfSafety * 1.25, marginOfSafety * 1.5];
      colorCellWithIDForZeroBasedRange('#current_price', range);
    } else {
      colorCellWithBackgroundColor('#current_price', Color.red());
    }

    let key = 'payback_time';
    updateHtmlWithValueForKey(data, key, /*commas=*/true);
    colorCellWithIDForZeroBasedRange('#' + key, [6, 8, 10]);
    if (!data[key] && data[key] !== 0) {
      colorCellWithBackgroundColor('#' + key, Color.red());
    }

    let ten_cap_key = 'ten_cap_price';
    let ten_cap_field_id = '#' + ten_cap_key;
    let current_price = data['current_price'];
    updateHtmlWithValueForKey(data, ten_cap_key, /*commas=*/true);
    if (!data[ten_cap_key] && data[ten_cap_key] !== 0) {
      colorCellWithBackgroundColor(ten_cap_field_id, Color.red());
    }
    if (current_price > data[ten_cap_key]) {
      colorCellWithBackgroundColor(ten_cap_field_id, Color.red());
    }
    else {
      colorCellWithBackgroundColor(ten_cap_field_id, Color.green());
    }

    updateHtmlWithValueForKey(data, 'average_volume', /*commas=*/true);
    let averageVolume = Number(data['average_volume']);
    let currentPriceValue = Number(data['current_price']);
    let minVolume = currentPriceValue <= 1.0 ? 1000000 : 500000;
    let averageVolumeColor = Number.isFinite(averageVolume) && averageVolume >= minVolume ? Color.green() : Color.red();
    colorCellWithBackgroundColor('#average_volume', averageVolumeColor);
    let sharesToHold = Number.isFinite(averageVolume)
      ? Math.round(averageVolume * 0.01).toLocaleString('en', {useGrouping:true})
      : 'N/A';
    $('#shares_to_hold').html(sharesToHold);
  }
});

function initializeFinancialTrendChart() {
  const chartElement = document.getElementById('financial-trend-chart');
  if (!chartElement || typeof Chart === 'undefined') {
    return;
  }

  const datasets = [
    { metricKey: 'eps', label: 'EPS Growth', borderColor: '#007bff', backgroundColor: 'rgba(0, 123, 255, 0.15)' },
    { metricKey: 'sales', label: 'Sales Growth', borderColor: '#17a2b8', backgroundColor: 'rgba(23, 162, 184, 0.15)' },
    { metricKey: 'equity', label: 'Equity Growth', borderColor: '#28a745', backgroundColor: 'rgba(40, 167, 69, 0.15)' },
    { metricKey: 'cash', label: 'Cash Flow Growth', borderColor: '#ff9800', backgroundColor: 'rgba(255, 152, 0, 0.15)' },
    { metricKey: 'roic', label: 'ROIC', borderColor: '#9c27b0', backgroundColor: 'rgba(156, 39, 176, 0.15)' }
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
            text: 'Growth (%)'
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
                label += 'No data';
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
  });

  financialTrendChart.update();
}

function updateFinancialTrendSummary(data) {
  const $summary = $('#financial-trend-summary');
  if (!$summary.length) {
    return;
  }

  if (!data) {
    $summary.text('Financial trend data will appear here after a successful search.');
    return;
  }

  const metricMap = {
    eps: 'EPS',
    sales: 'Sales',
    equity: 'Equity',
    cash: 'Cash Flow',
    roic: 'ROIC'
  };

  const highlights = Object.keys(metricMap).map(key => {
    const metricValues = Array.isArray(data[key]) ? data[key] : [];
    const oneYearValue = Number(metricValues[0]);
    if (!Number.isFinite(oneYearValue)) {
      return null;
    }
    return `${metricMap[key]} ${oneYearValue.toFixed(2)}% (1Y)`;
  }).filter(Boolean);

  if (!highlights.length) {
    $summary.text('Financial trend data is unavailable for this company.');
    return;
  }

  const summaryText = `1-year growth snapshot: ${highlights.slice(0, 3).join(', ')}.`;
  $summary.text(summaryText);
}

function sanitizeTickerInput(value) {
  if (!value) {
    return '';
  }
  return value.toUpperCase().replace(/[^A-Z.-]/g, '').slice(0, 8);
}

function updateHtmlWithValueForKey(data, key, commas) {
  let value = data[key];
  if (value === null || value === undefined || Number.isNaN(value)) {
    $('#' + key).html('Undefined');
    return;
  }
  if (commas) {
    value = Number(value);
    if (!Number.isFinite(value)) {
      $('#' + key).html('Undefined');
      return;
    }
    value = value.toLocaleString('en', {useGrouping:true});
  } else {
    value = Number(value);
    if (!Number.isFinite(value)) {
      $('#' + key).html('Undefined');
      return;
    }
    value = value.toFixed(2);
  }
  $('#' + key).html(value);
}

function updateBigFiveHtmlWithDataForKey(data, key) {
  let row_data = data[key];
  let suffixes = ['_1_val', '_3_val', '_5_val', '_max_val'];
  for (let i = 0; i < suffixes.length; i++) {
    let element_id = '#' + key + suffixes[i];
    let value = '-';
    if (Array.isArray(row_data) && i < row_data.length) {
      value = row_data[i];
    }
    $(element_id).html(value);

    if (value === '-' || value === null) {
      let color = (i === 0) ? Color.red() :  Color.white();
      $(element_id).css('background-color', color);
    } else {
      colorCellWithIDForRange(element_id, [0, 5, 10], true);
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
    let value = parseFloat($(id).html());
    if (Number.isNaN(value)) {
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
    let value = parseFloat($(id).html());
    if (Number.isNaN(value)) {
      $(id).text('-');
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
