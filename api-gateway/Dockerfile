FROM python:3.10-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# copy requirements & install via python -m pip to avoid pip mismatch
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install --no-cache-dir -r /app/requirements.txt

# copy source
COPY src/ /app/src/

EXPOSE 5000

# run the app as a module so `src` package imports resolve correctly
CMD ["python", "-m", "src.app"]