FROM 3-bookworm
# this Dockerfile is NOT complete!

# install signald and other APT dependencies
echo "deb [signed-by=/usr/share/keyrings/signald.gpg] https://updates.signald.org unstable main" > /etc/apt/sources.list.d/signald.list
wget -O /usr/share/keyrings/signald.gpg https://signald.org/signald.gpg
apt-get update
apt install -y signald supervisor

# install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord"]

