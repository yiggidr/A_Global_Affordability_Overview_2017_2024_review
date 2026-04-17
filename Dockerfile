FROM ubuntu:22.04

RUN apt-get -y update && \
    apt-get install -y python3-pip curl

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin/:$PATH"

COPY pyproject.toml .
RUN uv sync

COPY src ./src
COPY main.py .

ENV PYTHONPATH="/src"

CMD ["uv", "run", "streamlit", "run", "src/app/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0"]
