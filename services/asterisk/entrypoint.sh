#!/bin/bash

# Substitute environment variables in config files
envsubst < /etc/asterisk/custom/pjsip.conf.template > /etc/asterisk/pjsip.conf
envsubst < /etc/asterisk/custom/extensions.conf.template > /etc/asterisk/extensions.conf

# Copy other config files
cp /etc/asterisk/custom/modules.conf /etc/asterisk/modules.conf
cp /etc/asterisk/custom/http.conf /etc/asterisk/http.conf
cp /etc/asterisk/custom/ari.conf /etc/asterisk/ari.conf

# Start Asterisk
exec "$@"
