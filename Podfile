#### RedRunner ####
FROM docker-registry-default.cloud.registry.upshift.redhat.com/ccit/runner:base

LABEL maintainer=josiah@redhat.com

ADD runner /runner

ENTRYPOINT ["/entrypoint.sh"]
ADD entrypoint.sh /
