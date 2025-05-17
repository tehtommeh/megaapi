from shared.api import get_app
from shared.interfaces import AdditionRequest, AdditionResponse

app = get_app()

@app.post("/add")
def add_numbers(request: AdditionRequest) -> AdditionResponse:
    result = request.a + request.b
    return AdditionResponse(result=result) 