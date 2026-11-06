FROM ghcr.io/telekom/sutura@sha256:51a04d86c1d87049f01fb80fd6218bbebc21dce6180bbf97693cd741bce4bb2f AS sutura
FROM python:3.12-slim
COPY --from=sutura /nix /nix
COPY --from=sutura /bin/sutura /usr/local/bin/sutura
WORKDIR /app
COPY server.py source-fixture.json ./
COPY commerce-v1 ./commerce-v1
COPY public ./public
COPY LICENSE ./LICENSE
COPY third_party ./third_party
ENV PYTHONUNBUFFERED=1 PORT=8080 \
    SUTURA__RUNTIME__WORKING_SET_MAX_BYTES=134217728 \
    SUTURA__RUNTIME__ENGINE_WORKER_THREADS=2
USER 65532:65532
EXPOSE 8080
CMD ["python", "server.py"]
