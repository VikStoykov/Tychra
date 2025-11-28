import aiohttp
import logging

logger = logging.getLogger(__name__)

class CryptoProvider():
    """
    Provides Crypto Fear & Greed Index data.
    """

    URL = "https://api.alternative.me/fng/"

    EMOTION_MAP = {
        (0, 25): ("Extreme Fear", "😱"),
        (25, 45): ("Fear", "😨"),
        (45, 55): ("Neutral", "😐"),
        (55, 75): ("Greed", "😊"),
        (75, 101): ("Extreme Greed", "🤑")
    }

    @property
    def name(self):
        return "c"

    def required_keys(self, template = ""):
        keys = set()
        if f"{self.name}.index" in template:
            keys.add("index")
        if f"{self.name}.emotion" in template:
            keys.add("emotion")
        if f"{self.name}.emoji" in template:
            keys.add("emoji")
        if f"{self.name}.trend" in template:
            keys.add("trend")
        return keys

    def get_available_keys(self):
        return {"index", "emotion", "emoji", "trend", "timestamp"}

    def _get_emotion_and_emoji(self, index_value: int):
        for (low, high), (emotion, emoji) in self.EMOTION_MAP.items():
            if low <= index_value < high:
                return emotion, emoji
        return "Unknown", "❓"

    async def fetch(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(self.URL, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return await self._parse_alternative_response(data)
                    else:
                        logger.warning(f"Crypto Fear & Greed API returned status {response.status}")
                        return self._get_default_values()
        except Exception as e:
            logger.error(f"Error fetching Crypto Fear & Greed Index: {e}")
            return self._get_default_values()

    def _get_default_values(self):
        return {
            "index": 50,
            "emotion": "Unknown",
            "emoji": "❓",
            "trend": "→ stable",
            "timestamp": None
        }

    async def _parse_alternative_response(self, data: dict):
        try:
            # Alternative.me API structure: data[0] contains latest reading
            if "data" in data and len(data["data"]) > 0:
                current = data["data"][0]
                index_value = int(current.get("value", 50))
                
                emotion, emoji = self._get_emotion_and_emoji(index_value)
                
                trend = "→ stable"
                if len(data["data"]) > 1:
                    previous_value = int(data["data"][1].get("value", index_value))
                    if index_value > previous_value:
                        trend = "↗️ rising"
                    elif index_value < previous_value:
                        trend = "↘️ falling"

                return {
                    "index": index_value,
                    "emotion": emotion,
                    "emoji": emoji,
                    "trend": trend,
                    "timestamp": current.get("timestamp")
                }
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing Crypto Fear & Greed data: {e}")
            return self._get_default_values()
