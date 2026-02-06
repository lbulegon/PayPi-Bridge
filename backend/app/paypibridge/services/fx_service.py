"""
Foreign Exchange (FX) Service for Pi → BRL conversion.

This service handles currency conversion rates and provides
real-time or cached exchange rates for Pi to Brazilian Real (BRL).
"""

import os
import logging
import requests
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.cache import cache

logger = logging.getLogger(__name__)


class FXService:
    """
    Service for managing Pi to BRL exchange rates.
    Supports multiple rate providers and caching.
    """
    
    def __init__(self):
        self.cache_timeout = int(os.getenv('FX_CACHE_TIMEOUT', '300'))  # 5 minutes default
        self.provider = os.getenv('FX_PROVIDER', 'fixed')  # fixed, api, or custom
        self.fixed_rate = Decimal(os.getenv('FX_FIXED_RATE', '4.76'))  # Default rate
        self.api_url = os.getenv('FX_API_URL', '')
        self.api_key = os.getenv('FX_API_KEY', '')
    
    def get_rate(self, from_currency: str = 'PI', to_currency: str = 'BRL') -> Optional[Decimal]:
        """
        Get current exchange rate from Pi to BRL.
        
        Args:
            from_currency: Source currency (default: PI)
            to_currency: Target currency (default: BRL)
            
        Returns:
            Exchange rate as Decimal or None if unavailable
        """
        if from_currency != 'PI' or to_currency != 'BRL':
            logger.warning(
                f"Unsupported currency pair: {from_currency}/{to_currency}",
                extra={'from_currency': from_currency, 'to_currency': to_currency}
            )
            return None
        
        # Check cache first
        cache_key = f'fx_rate_{from_currency}_{to_currency}'
        cached_rate = cache.get(cache_key)
        if cached_rate:
            logger.debug(f"FX rate retrieved from cache", extra={'rate': str(cached_rate)})
            return Decimal(str(cached_rate))
        
        # Get fresh rate
        rate = self._fetch_rate()
        
        if rate:
            # Cache the rate
            cache.set(cache_key, str(rate), self.cache_timeout)
            logger.info(
                f"FX rate fetched and cached",
                extra={'rate': str(rate), 'provider': self.provider}
            )
        
        return rate
    
    def _fetch_rate(self) -> Optional[Decimal]:
        """Fetch exchange rate from configured provider."""
        if self.provider == 'fixed':
            return self.fixed_rate
        
        elif self.provider == 'api':
            return self._fetch_from_api()
        
        elif self.provider == 'custom':
            # Custom provider implementation
            return self._fetch_custom()
        
        else:
            logger.warning(f"Unknown FX provider: {self.provider}")
            return self.fixed_rate  # Fallback to fixed rate
    
    def _fetch_from_api(self) -> Optional[Decimal]:
        """Fetch rate from external API."""
        if not self.api_url:
            logger.warning("FX_API_URL not configured, using fixed rate")
            return self.fixed_rate
        
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.get(
                self.api_url,
                headers=headers,
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            # Adjust parsing based on API response format
            rate = Decimal(str(data.get('rate', data.get('price', self.fixed_rate))))
            
            return rate
            
        except Exception as e:
            logger.error(
                f"Error fetching FX rate from API: {e}",
                exc_info=True,
                extra={'api_url': self.api_url}
            )
            return self.fixed_rate  # Fallback
    
    def _fetch_custom(self) -> Optional[Decimal]:
        """Custom rate provider implementation."""
        # Placeholder for custom implementation
        # Could integrate with specific exchange rate APIs
        return self.fixed_rate
    
    def convert(self, amount_pi: Decimal, rate: Optional[Decimal] = None) -> Optional[Decimal]:
        """
        Convert Pi amount to BRL.
        
        Args:
            amount_pi: Amount in Pi
            rate: Optional exchange rate (if None, fetches current rate)
            
        Returns:
            Amount in BRL or None if conversion fails
        """
        if rate is None:
            rate = self.get_rate()
        
        if rate is None:
            logger.error("Cannot convert: exchange rate unavailable")
            return None
        
        try:
            amount_brl = amount_pi * rate
            # Round to 2 decimal places for BRL
            amount_brl = amount_brl.quantize(Decimal('0.01'))
            
            logger.debug(
                f"Currency conversion completed",
                extra={
                    'amount_pi': str(amount_pi),
                    'rate': str(rate),
                    'amount_brl': str(amount_brl)
                }
            )
            
            return amount_brl
            
        except Exception as e:
            logger.error(
                f"Error converting currency: {e}",
                exc_info=True,
                extra={'amount_pi': str(amount_pi), 'rate': str(rate)}
            )
            return None
    
    def get_quote(self, amount_pi: Decimal) -> Dict[str, Any]:
        """
        Get a complete FX quote for an amount.
        
        Args:
            amount_pi: Amount in Pi to quote
            
        Returns:
            Dict with rate, amount_brl, timestamp, and provider info
        """
        rate = self.get_rate()
        amount_brl = self.convert(amount_pi, rate) if rate else None
        
        return {
            'from_currency': 'PI',
            'to_currency': 'BRL',
            'amount_pi': str(amount_pi),
            'rate': str(rate) if rate else None,
            'amount_brl': str(amount_brl) if amount_brl else None,
            'timestamp': datetime.utcnow().isoformat(),
            'provider': self.provider,
            'cache_ttl': self.cache_timeout
        }


# Singleton instance
_fx_service_instance: Optional[FXService] = None


def get_fx_service() -> FXService:
    """Get singleton instance of FXService."""
    global _fx_service_instance
    if _fx_service_instance is None:
        _fx_service_instance = FXService()
    return _fx_service_instance
