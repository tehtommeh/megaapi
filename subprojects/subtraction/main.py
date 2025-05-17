from shared.api import get_app
from shared.interfaces import SubtractionRequest, SubtractionResponse

app = get_app()

@app.post("/subtract")
def subtract_numbers(request: SubtractionRequest) -> SubtractionResponse:
    result = request.a - request.b
    return SubtractionResponse(result=result) 