import pytest
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from django.test import TestCase, override_settings
from bcc_rates import SourceValue
from oxutils.currency.models import Currency, CurrencyState, AVAILABLES_CURRENCIES
from oxutils.currency.enums import CurrencySource
from oxutils.currency.utils import load_rates


class TestLoadRates(TestCase):
    """Tests for the load_rates utility function."""

    @patch('oxutils.currency.utils.BCCBankSource')
    def test_load_rates_success_bcc(self, mock_bcc_source):
        """Test successful rate loading from BCC."""
        mock_rates = [
            SourceValue(currency='USD', amount=Decimal('1.0')),
            SourceValue(currency='EUR', amount=Decimal('0.85')),
        ]
        mock_instance = Mock()
        mock_instance.sync.return_value = mock_rates
        mock_bcc_source.return_value = mock_instance

        rates, source = load_rates()

        assert rates == mock_rates
        assert source == CurrencySource.BCC
        mock_instance.sync.assert_called_once_with(cache=True)

    @patch('oxutils.currency.utils.time.sleep')
    @patch('oxutils.currency.utils.OXRBankSource')
    @patch('oxutils.currency.utils.BCCBankSource')
    @override_settings(OXI_BCC_FALLBACK_ON_OXR=True)
    def test_load_rates_fallback_to_oxr(self, mock_bcc_source, mock_oxr_source, mock_sleep):
        """Test fallback to OXR when BCC fails and fallback is enabled."""
        mock_bcc_instance = Mock()
        mock_bcc_instance.sync.side_effect = Exception("BCC API error")
        mock_bcc_source.return_value = mock_bcc_instance

        mock_oxr_rates = [
            SourceValue(currency='USD', amount=Decimal('1.0')),
            SourceValue(currency='GBP', amount=Decimal('0.75')),
        ]
        mock_oxr_instance = Mock()
        mock_oxr_instance.sync.return_value = mock_oxr_rates
        mock_oxr_source.return_value = mock_oxr_instance

        rates, source = load_rates()

        assert rates == mock_oxr_rates
        assert source == CurrencySource.OXR
        assert mock_bcc_instance.sync.call_count == 3
        assert mock_sleep.call_count == 2
        mock_oxr_instance.sync.assert_called_once_with(cache=True)

    @patch('oxutils.currency.utils.time.sleep')
    @patch('oxutils.currency.utils.BCCBankSource')
    @override_settings(OXI_BCC_FALLBACK_ON_OXR=False)
    def test_load_rates_bcc_failure_no_fallback(self, mock_bcc_source, mock_sleep):
        """Test that exception is raised when BCC fails and fallback is disabled."""
        mock_bcc_instance = Mock()
        mock_bcc_instance.sync.side_effect = Exception("BCC API error")
        mock_bcc_source.return_value = mock_bcc_instance

        with pytest.raises(Exception) as exc_info:
            load_rates()

        assert "Failed to load rates from BCC" in str(exc_info.value)
        assert mock_bcc_instance.sync.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('oxutils.currency.utils.time.sleep')
    @patch('oxutils.currency.utils.OXRBankSource')
    @patch('oxutils.currency.utils.BCCBankSource')
    @override_settings(OXI_BCC_FALLBACK_ON_OXR=True)
    def test_load_rates_both_sources_fail(self, mock_bcc_source, mock_oxr_source, mock_sleep):
        """Test that exception is raised when both BCC and OXR fail."""
        mock_bcc_instance = Mock()
        mock_bcc_instance.sync.side_effect = Exception("BCC API error")
        mock_bcc_source.return_value = mock_bcc_instance

        mock_oxr_instance = Mock()
        mock_oxr_instance.sync.side_effect = Exception("OXR API error")
        mock_oxr_source.return_value = mock_oxr_instance

        with pytest.raises(Exception) as exc_info:
            load_rates()

        assert "Failed to load rates from both BCC and OXR" in str(exc_info.value)
        assert mock_bcc_instance.sync.call_count == 3
        assert mock_sleep.call_count == 2

    @patch('oxutils.currency.utils.time.sleep')
    @patch('oxutils.currency.utils.BCCBankSource')
    def test_load_rates_retry_mechanism(self, mock_bcc_source, mock_sleep):
        """Test that the retry mechanism works correctly."""
        mock_bcc_instance = Mock()
        mock_bcc_instance.sync.side_effect = [
            Exception("Temporary error"),
            Exception("Temporary error"),
            [SourceValue(currency='USD', amount=Decimal('1.0'))]
        ]
        mock_bcc_source.return_value = mock_bcc_instance

        rates, source = load_rates()

        assert len(rates) == 1
        assert source == CurrencySource.BCC
        assert mock_bcc_instance.sync.call_count == 3
        assert mock_sleep.call_count == 2


class TestCurrencyModel(TestCase):
    """Tests for the Currency model."""

    def setUp(self):
        """Set up test data."""
        self.state = CurrencyState.objects.create(source=CurrencySource.BCC)

    def test_create_valid_currency(self):
        """Test creating a valid currency."""
        currency = Currency.objects.create(
            code='USD',
            rate=Decimal('1.0000'),
            state=self.state
        )
        
        assert currency.code == 'USD'
        assert currency.rate == Decimal('1.0000')
        assert currency.state == self.state

    def test_currency_str_representation(self):
        """Test string representation of currency."""
        currency = Currency.objects.create(
            code='EUR',
            rate=Decimal('0.8500'),
            state=self.state
        )
        
        assert str(currency) == 'EUR - 0.8500'

    def test_currency_invalid_code(self):
        """Test that invalid currency code raises error."""
        with pytest.raises(ValueError) as exc_info:
            Currency.objects.create(
                code='INVALID',
                rate=Decimal('1.0'),
                state=self.state
            )
        
        assert "Invalid currency code" in str(exc_info.value)

    def test_currency_invalid_rate_zero(self):
        """Test that zero rate raises error."""
        with pytest.raises(ValueError) as exc_info:
            Currency.objects.create(
                code='USD',
                rate=Decimal('0'),
                state=self.state
            )
        
        assert "Invalid currency rate" in str(exc_info.value)

    def test_currency_invalid_rate_negative(self):
        """Test that negative rate raises error."""
        with pytest.raises(ValueError) as exc_info:
            Currency.objects.create(
                code='USD',
                rate=Decimal('-1.0'),
                state=self.state
            )
        
        assert "Invalid currency rate" in str(exc_info.value)

    def test_currency_ordering(self):
        """Test that currencies are ordered by code."""
        Currency.objects.create(code='USD', rate=Decimal('1.0'), state=self.state)
        Currency.objects.create(code='EUR', rate=Decimal('0.85'), state=self.state)
        Currency.objects.create(code='GBP', rate=Decimal('0.75'), state=self.state)
        
        currencies = list(Currency.objects.all())
        codes = [c.code for c in currencies]
        
        assert codes == ['EUR', 'GBP', 'USD']


class TestCurrencyStateModel(TestCase):
    """Tests for the CurrencyState model."""

    @patch('oxutils.currency.models.load_rates')
    def test_sync_success(self, mock_load_rates):
        """Test successful currency state sync."""
        mock_rates = [
            SourceValue(currency='USD', amount=Decimal('1.0000')),
            SourceValue(currency='EUR', amount=Decimal('0.8500')),
            SourceValue(currency='GBP', amount=Decimal('0.7500')),
        ]
        mock_load_rates.return_value = (mock_rates, CurrencySource.BCC)

        state = CurrencyState.sync()

        assert state is not None
        assert state.source == CurrencySource.BCC
        assert state.currencies.count() == 3
        
        usd = state.currencies.get(code='USD')
        assert usd.rate == Decimal('1.0000')
        
        eur = state.currencies.get(code='EUR')
        assert eur.rate == Decimal('0.8500')

    @patch('oxutils.currency.models.load_rates')
    def test_sync_with_oxr_source(self, mock_load_rates):
        """Test sync with OXR as source."""
        mock_rates = [
            SourceValue(currency='USD', amount=Decimal('1.0000')),
        ]
        mock_load_rates.return_value = (mock_rates, CurrencySource.OXR)

        state = CurrencyState.sync()

        assert state.source == CurrencySource.OXR

    @patch('oxutils.currency.models.load_rates')
    def test_sync_no_rates(self, mock_load_rates):
        """Test that sync raises error when no rates are returned."""
        mock_load_rates.return_value = ([], CurrencySource.BCC)

        with pytest.raises(ValueError) as exc_info:
            CurrencyState.sync()
        
        assert "No rates found" in str(exc_info.value)

    @patch('oxutils.currency.models.load_rates')
    def test_sync_creates_multiple_states(self, mock_load_rates):
        """Test that multiple syncs create separate states."""
        mock_rates = [
            SourceValue(currency='USD', amount=Decimal('1.0000')),
        ]
        mock_load_rates.return_value = (mock_rates, CurrencySource.BCC)

        state1 = CurrencyState.sync()
        state2 = CurrencyState.sync()

        assert state1.id != state2.id
        assert CurrencyState.objects.count() == 2

    @patch('oxutils.currency.models.load_rates')
    def test_latest_manager_method(self, mock_load_rates):
        """Test the latest() manager method."""
        mock_rates = [
            SourceValue(currency='USD', amount=Decimal('1.0000')),
        ]
        mock_load_rates.return_value = (mock_rates, CurrencySource.BCC)

        state1 = CurrencyState.sync()
        state2 = CurrencyState.sync()
        
        latest = CurrencyState.objects.latest()
        
        assert latest.id == state2.id
        assert latest.currencies.count() == 1

    @patch('oxutils.currency.models.load_rates')
    def test_sync_with_large_dataset(self, mock_load_rates):
        """Test sync with a large number of currencies."""
        mock_rates = [
            SourceValue(currency=code, amount=Decimal('1.0000'))
            for code in ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD']
        ]
        mock_load_rates.return_value = (mock_rates, CurrencySource.BCC)

        state = CurrencyState.sync()
        
        assert state.currencies.count() == 6
        assert CurrencyState.objects.count() == 1


class TestAvailableCurrencies(TestCase):
    """Tests for available currencies constant."""

    def test_available_currencies_list(self):
        """Test that AVAILABLES_CURRENCIES contains expected currencies."""
        expected_currencies = [
            'USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 
            'CNY', 'XAF', 'AOA', 'RWF', 'UGX', 'TZS', 'ZAR', 
            'ZMW', 'BIF', 'XDR'
        ]
        
        for currency in expected_currencies:
            assert currency in AVAILABLES_CURRENCIES

    def test_available_currencies_count(self):
        """Test the number of available currencies."""
        assert len(AVAILABLES_CURRENCIES) == 17
