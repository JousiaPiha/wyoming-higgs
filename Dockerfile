FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY wyoming_higgs ./wyoming_higgs

RUN pip install --no-cache-dir .

ENTRYPOINT ["wyoming-higgs"]
CMD ["--uri", "tcp://0.0.0.0:10200"]
