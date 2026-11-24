import httpx2

from agritech.data.isdasoil import IsdaSoilClient, parse_property


def response(name, value, unit, low, high):
    """Shape of a real iSDAsoil v2 response (Kandi, 21 November 2026)."""
    return {
        "property": {
            name: [
                {
                    "value": {"unit": unit, "type": "float", "value": value},
                    "depth": {"value": "0-20", "unit": "cm"},
                    "uncertainty": [
                        {
                            "confidence_interval": "50%",
                            "lower_bound": 0,
                            "upper_bound": 0,
                        },
                        {
                            "confidence_interval": "90%",
                            "lower_bound": low,
                            "upper_bound": high,
                        },
                    ],
                }
            ]
        }
    }


def test_value_unit_and_90_percent_interval():
    value = parse_property(
        response("clay_content", 16, "%", 9.4, 22.6), "clay_content", "0-20"
    )
    assert (value.value, value.unit, value.low, value.high) == (16, "%", 9.4, 22.6)


def test_ph_has_no_unit():
    value = parse_property(response("ph", 6.1, None, 5.9, 6.3), "ph", "0-20")
    assert (value.value, value.unit) == (6.1, "")


def test_zero_bounds_are_no_uncertainty():
    # Returned for the pH of Kandi at 20-50 cm and of Karimama.
    value = parse_property(response("ph", 6.2, None, 0, 0), "ph", "20-50")
    assert value.value == 6.2
    assert (value.low, value.high) == (None, None)


def test_absent_property_is_missing_not_zero():
    value = parse_property({"property": {}}, "ph", "0-20")
    assert value.value is None


def client_with(handler):
    return IsdaSoilClient(
        "user", "secret", "https://isda.test", httpx2.MockTransport(handler)
    )


def test_one_login_then_one_call_per_property():
    calls = []

    def handler(request):
        calls.append((request.method, request.url.path, dict(request.url.params)))
        if request.url.path == "/login":
            return httpx2.Response(200, json={"access_token": "t1"})
        assert request.headers["Authorization"] == "Bearer t1"
        return httpx2.Response(200, json=response("ph", 6.1, None, 5.9, 6.3))

    client = client_with(handler)
    client.fetch(11.279, 2.94, "0-20", "ph")
    client.fetch(11.279, 2.94, "0-20", "clay_content")
    soil = "/isdasoil/v2/soilproperty"
    assert [c[1] for c in calls] == ["/login", soil, soil]
    assert calls[1][2] == {
        "lon": "2.94",
        "lat": "11.279",
        "depth": "0-20",
        "property": "ph",
    }


def test_expired_token_logs_in_again_once():
    tokens = iter(["old", "new"])

    def handler(request):
        if request.url.path == "/login":
            return httpx2.Response(200, json={"access_token": next(tokens)})
        if request.headers["Authorization"] == "Bearer old":
            return httpx2.Response(401)
        return httpx2.Response(200, json=response("ph", 6.1, None, 5.9, 6.3))

    payload = client_with(handler).fetch(11.279, 2.94, "0-20", "ph")
    assert parse_property(payload, "ph", "0-20").value == 6.1
