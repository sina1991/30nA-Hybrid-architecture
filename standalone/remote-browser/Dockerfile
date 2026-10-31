# syntax=docker/dockerfile:1
FROM python@sha256:1148dbb014615300fa7e713b2f94f550c0d1c69780c0805f84f093ceee34dd0b
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock /app/
RUN --mount=type=secret,id=proxy_ca,required=true PIP_CERT=/run/secrets/proxy_ca pip install --no-cache-dir --require-hashes -r requirements.lock
COPY --chmod=0644 egress.py transport.py /app/
USER 1000:1000
EXPOSE 8080 3128
CMD ["python","egress.py"]
