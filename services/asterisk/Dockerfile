FROM debian:bullseye-slim

# Install Asterisk and dependencies
RUN apt-get update && apt-get install -y \
    asterisk \
    asterisk-modules \
    asterisk-core-sounds-es-wav \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy configuration files
COPY config/ /etc/asterisk/custom/
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Expose ports
# SIP
EXPOSE 5060/udp
EXPOSE 5060/tcp
# WebSocket
EXPOSE 8088
# RTP
EXPOSE 10000-10100/udp

ENTRYPOINT ["/entrypoint.sh"]
CMD ["asterisk", "-f"]
