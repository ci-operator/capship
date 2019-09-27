#!/bin/bash
if [ `id -u` -gt 1000000 ]; then
    echo "runner:x:`id -u`:`id -g`:,,,:/runner:/bin/bash" > /tmp/passwd
    cat /tmp/passwd >> /etc/passwd
    rm /tmp/passwd
fi

echo Running: $@
exec /bin/tini -- $@
