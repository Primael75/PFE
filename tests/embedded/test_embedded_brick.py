import subprocess
import sys

DRONE_LIBRARIES = ("mavsdk", "pymavlink", "serial")


def test_importing_the_brick_loads_no_drone_library():
    # A fresh interpreter: other tests cannot have loaded these modules already.
    check = (
        "import sys, agritech.embedded; "
        f"print([n for n in {DRONE_LIBRARIES!r} if n in sys.modules])"
    )

    result = subprocess.run(
        [sys.executable, "-c", check], capture_output=True, text=True, check=True
    )

    assert result.stdout.strip() == "[]"
