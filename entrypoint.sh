#!/bin/bash
if [ `id -u` -gt 1000000 ]; then
    echo "runner:x:`id -u`:`id -g`:,,,:/runner:/bin/bash" > /tmp/passwd
    cat /tmp/passwd >> /etc/passwd
    rm /tmp/passwd
fi

if [ -e /ansible/requirements.yml ]; then
    ansible-galaxy install -r /ansible/requirements.yml -p /.ansible/roles
fi

echo Running: $@
exec /bin/tini -- $@
