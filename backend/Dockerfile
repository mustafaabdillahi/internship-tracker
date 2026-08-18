FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .
COPY . .
COPY entrypoint.sh .
RUN chmod + entrypoint.sh
CMD ["./entrypoint.sh"]