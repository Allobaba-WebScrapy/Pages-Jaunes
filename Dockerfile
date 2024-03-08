# SeleniumBase Docker Image
FROM ubuntu:18.04

#=======================================
# Install Python and Basic Python Tools
#=======================================
RUN apt-get -o Acquire::Check-Valid-Until=false -o Acquire::Check-Date=false update
RUN apt-get install -y python3 python3-pip python3-setuptools python3-dev python-distribute
RUN alias python=python3
RUN echo "alias python=python3" >> ~/.bashrc

#=================================
# Install Bash Command Line Tools
#=================================
RUN apt-get -qy --no-install-recommends install \
    sudo \
    unzip \
    wget \
    curl \
    libxi6 \
    libgconf-2-4 \
    vim \
    xvfb \
  && rm -rf /var/lib/apt/lists/*

#================
# Install Chrome
#================
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    apt-get -yqq update && \
    apt-get -yqq install google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*


#===========================
# Configure Virtual Display
#===========================
RUN set -e
RUN echo "Starting X virtual framebuffer (Xvfb) in background..."
# RUN Xvfb -ac :99 -screen 0 600, 1200 1280x1024x16 > /dev/null 2>&1 &
RUN Xvfb -ac :99 -screen 0 600x1200x16 > /dev/null 2>&1 &
RUN export DISPLAY=:99
RUN exec "$@"

#=======================
# Update Python Version
#=======================
RUN apt-get update -y
RUN apt-get -qy --no-install-recommends install python3.8
RUN rm /usr/bin/python3
RUN ln -s python3.8 /usr/bin/python3

#=============================================
# Allow Special Characters in Python Programs
#=============================================
RUN export PYTHONIOENCODING=utf8
RUN echo "export PYTHONIOENCODING=utf8" >> ~/.bashrc

#=====================
# Set up SeleniumBase
#=====================
COPY sbase /SeleniumBase/sbase/
COPY seleniumbase /SeleniumBase/seleniumbase/
COPY examples /SeleniumBase/examples/
COPY integrations /SeleniumBase/integrations/
COPY requirements.txt /SeleniumBase/requirements.txt
COPY setup.py /SeleniumBase/setup.py
RUN find . -name '*.pyc' -delete
RUN find . -name __pycache__ -delete
RUN pip3 install --upgrade pip setuptools wheel
RUN cd /SeleniumBase && ls && pip3 install -r requirements.txt --upgrade
RUN cd /SeleniumBase && pip3 install .

#=====================
# Download WebDrivers
#=====================
RUN wget https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz
RUN tar -xvzf geckodriver-v0.34.0-linux64.tar.gz
RUN chmod +x geckodriver
RUN mv geckodriver /usr/local/bin/
RUN wget https://chromedriver.storage.googleapis.com/72.0.3626.69/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN chmod +x chromedriver
RUN mv chromedriver /usr/local/bin/

#==========================================
# Create entrypoint and grab example tests
#==========================================
COPY integrations/docker/docker-entrypoint.sh /
COPY integrations/docker/run_docker_test_in_firefox.sh /
COPY integrations/docker/run_docker_test_in_chrome.sh /
RUN chmod +x *.sh
COPY integrations/docker/docker_config.cfg /SeleniumBase/examples/
ENTRYPOINT ["/docker-entrypoint.sh"]


COPY ./index.py .

CMD ["/bin/bash && python3", "index.py"]