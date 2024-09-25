FROM python:3.12-bookworm

ADD requirements.txt /requirements.txt
ADD src /app
WORKDIR /app

# Install GDAL dependencies and Python development headers
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        binutils \
        libproj-dev \
        libgdal-dev && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/* 

RUN pip install --no-cache-dir -r /requirements.txt

EXPOSE 9000

CMD ["gunicorn", "--bind", ":9000", "app:app", "--log-level", "info", "-w", "4"]