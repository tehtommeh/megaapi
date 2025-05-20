FROM python:3.13
RUN apt update && apt install -y ffmpeg cmake
WORKDIR /app
COPY --from=shared . ../shared
RUN pip install --no-cache-dir -r ../shared/requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 