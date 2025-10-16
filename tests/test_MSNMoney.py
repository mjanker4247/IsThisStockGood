"""Tests for the MSNMoney.py functions."""


import os
import unittest
from unittest import mock

from isthisstockgood.Active.MSNMoney import MSNMoney


class MSNMoneyTest(unittest.TestCase):

  def setUp(self):
    self._environ_patcher = mock.patch.dict(os.environ, {"ISG_MSN_MONEY_API_KEY": "test-key"})
    self._environ_patcher.start()

  def tearDown(self):
    self._environ_patcher.stop()

  def test_parse_pe_ratios_should_return_false_when_no_data(self):
    self.assertFalse(MSNMoney('DUMMY')._parse_pe_ratios([]))

  def test_parse_pe_ratios_should_return_false_if_too_few_pe_ratios(self):
    msn = MSNMoney('DUMMY')
    payload = {
      'companyMetrics' : [
        {
          'fiscalPeriodType' : 'Annual',
          'priceToEarningsRatio' : 22.5
        },
      ]
    }
    self.assertFalse(msn._parse_pe_ratios(payload['companyMetrics']))

  def test_parse_pe_ratios_should_properly_calculate_pe_ratios(self):
    msn = MSNMoney('DUMMY')
    payload = {
      'companyMetrics' : [
        {
          'fiscalPeriodType' : 'Annual',
          'priceToEarningsRatio' : 18.5
        },
        {
          'fiscalPeriodType' : 'Annual',
          'priceToEarningsRatio' : 23.0
        },
        {
          'fiscalPeriodType' : 'Annual',
          'priceToEarningsRatio' : 21.0
        },
        {
          'fiscalPeriodType' : 'Annual',
          'priceToEarningsRatio' : 19.5
        },
        {
          'fiscalPeriodType' : 'Annual',
          'priceToEarningsRatio' : 24.5
        },
        {
          'fiscalPeriodType' : 'Annual',
          'priceToEarningsRatio' : 26.5
        },
      ]
    }
    msn._parse_pe_ratios(payload['companyMetrics'])
    self.assertEqual(msn.pe_high, 26.5)
    self.assertEqual(msn.pe_low, 19.5)
