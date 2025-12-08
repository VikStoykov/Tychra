import aiohttp
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List
from quickchart import QuickChart

logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    Generates Fear & Greed Index charts with rate limiting.
    """

    MARKET_API_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    CRYPTO_API_URL = "https://api.alternative.me/fng/?limit={days}"

    def __init__(self):
        self._lock = asyncio.Lock()
        self._is_generating = False

    async def is_busy(self) -> bool:
        """
        Check if chart generation is in progress.
        """
        return self._is_generating

    async def _fetch_market_data(self, days: int) -> Optional[Dict]:
        """
        Fetch historical market F&G data from CNN API.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Referer': 'https://www.cnn.com/markets/fear-and-greed'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.MARKET_API_URL, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Fetched market data: {len(data.get('fear_and_greed_historical', {}).get('data', []))} records")
                        return data
                    elif response.status == 418:
                        logger.error(f"⛔ Market API blocked request (418 - rate limited or bot detected)")
                        return None
                    else:
                        logger.error(f"⛔ Market API returned status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"⛔ Error fetching market data: {e}")
            return None

    async def _fetch_crypto_data(self, days: int) -> Optional[Dict]:
        """
        Fetch historical crypto F&G data from Alternative.me API.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json'
            }

            url = self.CRYPTO_API_URL.format(days=days)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Fetched crypto data: {len(data.get('data', []))} records")
                        return data
                    else:
                        logger.error(f"⛔ Crypto API returned status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"⛔ Error fetching crypto data: {e}")
            return None

    def _parse_market_data(self, data: Dict, days: int) -> tuple[List[str], List[float]]:
        """
        Parse CNN market data into labels and values.
        """
        try:
            historical = data.get('fear_and_greed_historical', {}).get('data', [])

            # Get last N days
            records = historical[-days:] if len(historical) > days else historical

            labels = []
            values = []

            for record in records:
                # Parse timestamp (format: "2024-12-01" or unix timestamp)
                timestamp = record.get('x')
                if isinstance(timestamp, str):
                    date_obj = datetime.strptime(timestamp.split('T')[0], '%Y-%m-%d')
                    labels.append(date_obj.strftime('%m/%d'))
                else:
                    # Unix timestamp in milliseconds
                    date_obj = datetime.fromtimestamp(timestamp / 1000)
                    labels.append(date_obj.strftime('%m/%d'))

                # Get value
                value = float(record.get('y', 0))
                values.append(value)

            return labels, values
        except Exception as e:
            logger.error(f"⛔ Error parsing market data: {e}")
            return [], []

    def _parse_crypto_data(self, data: Dict, days: int) -> tuple[List[str], List[float]]:
        """
        Parse Alternative.me crypto data into labels and values.
        """
        try:
            records = data.get('data', [])

            # Reverse because API returns newest first
            records = list(reversed(records[:days]))

            labels = []
            values = []

            for record in records:
                # Parse timestamp (unix timestamp)
                timestamp = int(record.get('timestamp', 0))
                date_obj = datetime.fromtimestamp(timestamp)
                labels.append(date_obj.strftime('%m/%d'))
                
                # Get value
                value = float(record.get('value', 0))
                values.append(value)

            return labels, values
        except Exception as e:
            logger.error(f"⛔ Error parsing crypto data: {e}")
            return [], []

    def _generate_chart_config(self, labels: List[str], values: List[float], title: str) -> Dict:
        """
        Generate QuickChart configuration with color-coded fear/greed zones.
        """
        return {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'label': 'Fear & Greed Index',
                    'data': values,
                    'fill': False,
                    'borderColor': 'rgb(255, 255, 255)',
                    'backgroundColor': 'rgb(255, 255, 255)',
                    'borderWidth': 3,
                    'pointBackgroundColor': values,  # Dynamic coloring per point
                    'pointBorderColor': '#fff',
                    'pointBorderWidth': 2,
                    'pointRadius': 5,
                    'pointHoverRadius': 7,
                    'tension': 0.4
                }]
            },
            'options': {
                'title': {
                    'display': True,
                    'text': title,
                    'fontSize': 20,
                    'fontColor': '#fff',
                    'fontStyle': 'bold'
                },
                'legend': {
                    'display': True,
                    'labels': {
                        'fontColor': '#fff',
                        'fontSize': 14
                    }
                },
                'annotation': {
                    'annotations': [
                        {
                            'type': 'box',
                            'yScaleID': 'y-axis-0',
                            'yMin': 0,
                            'yMax': 25,
                            'backgroundColor': 'rgba(220, 38, 38, 0.15)',
                            'borderWidth': 0
                        },
                        {
                            'type': 'box',
                            'yScaleID': 'y-axis-0',
                            'yMin': 25,
                            'yMax': 45,
                            'backgroundColor': 'rgba(251, 146, 60, 0.15)',
                            'borderWidth': 0
                        },
                        {
                            'type': 'box',
                            'yScaleID': 'y-axis-0',
                            'yMin': 45,
                            'yMax': 55,
                            'backgroundColor': 'rgba(250, 204, 21, 0.15)',
                            'borderWidth': 0
                        },
                        {
                            'type': 'box',
                            'yScaleID': 'y-axis-0',
                            'yMin': 55,
                            'yMax': 75,
                            'backgroundColor': 'rgba(134, 239, 172, 0.15)',
                            'borderWidth': 0
                        },
                        {
                            'type': 'box',
                            'yScaleID': 'y-axis-0',
                            'yMin': 75,
                            'yMax': 100,
                            'backgroundColor': 'rgba(34, 197, 94, 0.15)',
                            'borderWidth': 0
                        }
                    ]
                },
                'scales': {
                    'yAxes': [{
                        'id': 'y-axis-0',
                        'ticks': {
                            'beginAtZero': True,
                            'max': 100,
                            'stepSize': 25,
                            'fontColor': '#fff',
                            'fontSize': 12
                        },
                        'gridLines': {
                            'color': 'rgba(255, 255, 255, 0.1)',
                            'lineWidth': 1
                        },
                        'scaleLabel': {
                            'display': True,
                            'labelString': 'Fear ← Index Value (0-100) → Greed',
                            'fontColor': '#fff',
                            'fontSize': 14,
                            'fontStyle': 'bold'
                        }
                    }],
                    'xAxes': [{
                        'ticks': {
                            'fontColor': '#fff',
                            'fontSize': 11,
                            'maxRotation': 45,
                            'minRotation': 45
                        },
                        'gridLines': {
                            'color': 'rgba(255, 255, 255, 0.05)',
                            'lineWidth': 1
                        },
                        'scaleLabel': {
                            'display': True,
                            'labelString': 'Date',
                            'fontColor': '#fff',
                            'fontSize': 14
                        }
                    }]
                }
            }
        }

    async def generate_chart(self, days: int = 10, provider: str = "market") -> Optional[str]:
        """
        Generate F&G index chart and return URL.

        Args:
            days: Number of days to include (default 10)
            provider: "market" for stock or "crypto" for cryptocurrency (default "market")

        Returns:
            Chart URL or None if generation failed
        """
        # Rate limiting - only one chart generation at a time
        if self._is_generating:
            logger.warning("⚠️ Chart generation already in progress, rejecting request")
            return None

        async with self._lock:
            self._is_generating = True
            try:
                logger.info(f"🎨 Generating {provider} chart for last {days} days")

                # Fetch data based on provider
                if provider == "crypto":
                    data = await self._fetch_crypto_data(days)
                    if not data:
                        return None
                    labels, values = self._parse_crypto_data(data, days)
                    title = f"Crypto Fear & Greed Index (Last {days} Days)"
                else:  # market
                    data = await self._fetch_market_data(days)
                    if not data:
                        return None
                    labels, values = self._parse_market_data(data, days)
                    title = f"Stock Market Fear & Greed Index (Last {days} Days)"

                if not labels or not values:
                    logger.error("⛔ No data to generate chart")
                    return None

                # Generate chart
                chart_config = self._generate_chart_config(labels, values, title)

                qc = QuickChart()
                qc.width = 800
                qc.height = 400
                qc.background_color = '#1e1e1e'
                qc.config = chart_config

                # Get short URL
                try:
                    url = qc.get_short_url()
                    logger.info(f"✅ Chart generated: {url}")
                    return url
                except Exception as url_error:
                    logger.error(f"⛔ Error getting short URL: {url_error}")
                    # Fallback to regular URL
                    try:
                        url = qc.get_url()
                        logger.info(f"✅ Chart generated (long URL): {url[:100]}...")
                        return url
                    except Exception as fallback_error:
                        logger.error(f"⛔ Error getting URL: {fallback_error}")
                        return None

            except Exception as e:
                logger.error(f"⛔ Error generating chart: {e}")
                return None
            finally:
                self._is_generating = False
