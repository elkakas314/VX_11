FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl git && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY . /workspace

RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install uvicorn fastapi httpx pydantic pytest requests

EXPOSE 52111 52112 52113 52114 52115 52116 52117 52118

CMD ["/bin/bash"]
