FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    unzip \
    apt-transport-https \
    ca-certificates \
    --no-install-recommends && \
    apt-get clean

ENV TZ=Asia/Bangkok
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && apt-get install -y google-chrome-stable=129.0.6668.89-1

RUN CHROMEDRIVER_VERSION=129.0.6668.89 && \
    wget -q "https://storage.googleapis.com/chrome-for-testing-public/${CHROMEDRIVER_VERSION}/linux64/chromedriver-linux64.zip" -O /tmp/chromedriver.zip && \
    if [ -s /tmp/chromedriver.zip ]; then \
        echo "Download successful"; \
        unzip /tmp/chromedriver.zip -d /usr/local/bin/; \
        chmod +x /usr/local/bin/chromedriver; \
        echo "Unzip successful"; \
    else \
        echo "Download failed or file is empty" && exit 1; \
    fi && \
    rm /tmp/chromedriver.zip

ENV PATH="/usr/local/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
