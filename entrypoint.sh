#!/bin/bash
if [ -e /ansible/requirements.yml ]; then
  echo "Installing roles for local ansible user"
  ansible-galaxy install -i -r /ansible/requirements.yml -p /ansible/roles
fi
if [ `id -u` -gt 1000000 ]; then
  echo "runner:x:`id -u`:`id -g`:,,,:/runner:/bin/bash" > /tmp/passwd
  cat /tmp/passwd >> /etc/passwd
  rm /tmp/passwd
  if [ -e /ansible/requirements.yml ]; then
    echo "Installing roles for runner"
    cp -rv /ansible/roles /runner/components/
    cp -rv /ansible/roles /.ansible/
  fi
fi
echo Running: $@
exec /bin/tini -- $@
