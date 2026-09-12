import csv
from typing import Dict, Tuple, Optional


class CurrencyNormalizer:
    """Handles fixed, dated foreign-currency conversions using exchange_rates.csv."""

    def __init__(self, exchange_rates_csv: str = "dataset/exchange_rates.csv"):
        self.rates: Dict[Tuple[str, str, str], float] = {}
        self._load_rates(exchange_rates_csv)

    def _load_rates(self, file_path: str) -> None:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dt = row["rate_date"].strip()
                from_c = row["from_currency"].strip()
                to_c = row["to_currency"].strip()
                rate = float(row["rate"].strip())
                self.rates[(dt, from_c, to_c)] = rate

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
        rate_date: str,
    ) -> Tuple[float, float, str]:
        """
        Converts an amount from one currency to another using the exact fixed rate for rate_date.
        Returns: (converted_amount, rate_used, rate_date_used)
        """
        if from_currency == to_currency:
            return amount, 1.0, rate_date

        key = (rate_date, from_currency, to_currency)
        if key in self.rates:
            rate = self.rates[key]
            return amount * rate, rate, rate_date

        # Check for direct inverse if available
        inv_key = (rate_date, to_currency, from_currency)
        if inv_key in self.rates:
            inv_rate = self.rates[inv_key]
            rate = 1.0 / inv_rate
            return amount * rate, rate, rate_date

        raise ValueError(
            f"No exchange rate found for {from_currency} -> {to_currency} on {rate_date}"
        )

    def get_rate(self, from_currency: str, to_currency: str, rate_date: str) -> Optional[float]:
        if from_currency == to_currency:
            return 1.0
        key = (rate_date, from_currency, to_currency)
        if key in self.rates:
            return self.rates[key]
        inv_key = (rate_date, to_currency, from_currency)
        if inv_key in self.rates:
            return 1.0 / self.rates[inv_key]
        return None
