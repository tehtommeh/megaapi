from shared.api import get_app
from shared.interfaces import WaitRequest, WaitResponse
from datetime import datetime, UTC
import time

app = get_app()

@app.post("/wait")
def wait(request: WaitRequest) -> WaitResponse:
    start_time = datetime.now(UTC).isoformat()
    time.sleep(request.wait_time)
    end_time = datetime.now(UTC).isoformat()
    return WaitResponse(waited=True, start_time=start_time, end_time=end_time) 