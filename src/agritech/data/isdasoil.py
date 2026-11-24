"""iSDAsoil v2 soil properties at a point, through the official API.

Values are machine-learning predictions at 30 m, not laboratory analyses;
each comes with confidence intervals. See docs/data/isdasoil.md.
"""

import logging
from dataclasses import dataclass

import httpx2

logger = logging.getLogger(__name__)

API_URL = "https://api.isda-africa.com"
DEPTHS = ("0-20", "20-50")
# The widest interval the API returns: a narrower one would overstate precision.
CONFIDENCE = "90%"


@dataclass(frozen=True)
class SoilValue:
    property: str
    depth_cm: str
    value: float | str | None
    unit: str
    low: float | None
    high: float | None


def parse_property(payload: dict, name: str, depth_cm: str) -> SoilValue:
    """Value, unit and 90 % interval of one property in an API response."""
    entries = payload.get("property", {}).get(name) or []
    if not entries:
        return SoilValue(name, depth_cm, None, "", None, None)
    entry = entries[0]
    value = entry["value"].get("value")
    low = high = None
    for interval in entry.get("uncertainty") or []:
        if interval.get("confidence_interval") == CONFIDENCE:
            low, high = interval.get("lower_bound"), interval.get("upper_bound")
    # The API sometimes returns 0-0 bounds (seen for pH): an interval that
    # does not contain the value is no uncertainty at all.
    numeric = isinstance(value, int | float)
    if not numeric or low is None or high is None or not low <= value <= high:
        if low is not None:
            logger.warning("%s %s cm: bounds %s-%s ignored", name, depth_cm, low, high)
        low = high = None
    return SoilValue(name, depth_cm, value, entry["value"].get("unit") or "", low, high)


class IsdaSoilClient:
    """Logs in with an iSDA account and fetches one property per call.

    The API keeps only the last value of a repeated `property` parameter, so
    several properties cannot share a call.
    """

    def __init__(
        self,
        username: str,
        password: str,
        base_url: str = API_URL,
        transport: httpx2.BaseTransport | None = None,
    ):
        self._credentials = {"username": username, "password": password}
        self._client = httpx2.Client(base_url=base_url, transport=transport, timeout=60)
        self._token: str | None = None

    def close(self) -> None:
        self._client.close()

    def fetch(self, lat: float, lon: float, depth_cm: str, name: str) -> dict:
        """Raw API response for one property at one point and depth."""
        params = {"lon": lon, "lat": lat, "depth": depth_cm, "property": name}
        response = self._get(params)
        # The token lasts one hour: log in again once if it expired.
        if response.status_code == 401:
            self._token = None
            response = self._get(params)
        response.raise_for_status()
        return response.json()

    def _get(self, params: dict) -> httpx2.Response:
        if self._token is None:
            self._token = self._login()
        return self._client.get(
            "/isdasoil/v2/soilproperty",
            params=params,
            headers={"Authorization": f"Bearer {self._token}"},
        )

    def _login(self) -> str:
        response = self._client.post("/login", data=self._credentials)
        response.raise_for_status()
        return response.json()["access_token"]
