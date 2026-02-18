FROM python:3.10-slim

# 1. Fix Debian Sources to allow non-free (Required for Standard MIBs)
# This handles both old (sources.list) and new (debian.sources) formats
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i 's/Components: main/Components: main contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources; \
    elif [ -f /etc/apt/sources.list ]; then \
      sed -i 's/main/main contrib non-free/g' /etc/apt/sources.list; \
    fi

# 2. Install System Dependencies & MIB Downloader
RUN apt-get update && apt-get install -y \
    snmp \
    snmp-mibs-downloader \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 3. Download Standard MIBs (RFCs, IANA, etc.)
# This populates /usr/share/snmp/mibs/
RUN download-mibs

# 4. Configure Net-SNMP
# - Comment out the default 'mibs :' line which disables loading
# - Add our custom directory
# - Load ALL mibs by default
RUN sed -i 's/^mibs :/# mibs :/' /etc/snmp/snmp.conf && \
    echo "mibdirs +/usr/share/snmp/mibs/custom" >> /etc/snmp/snmp.conf && \
    echo "mibs +ALL" >> /etc/snmp/snmp.conf

# 5. Setup App
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy Code
COPY . .

# 7. Environment Defaults
ENV MODULE_NAME="main"
ENV VARIABLE_NAME="app"
ENV PORT=8000

# 8. Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
