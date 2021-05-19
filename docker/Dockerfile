FROM ubuntu:20.04
LABEL maintainer="aes"

# Install dependencies.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       software-properties-common sudo cron \
    && rm -Rf /var/lib/apt/lists/* \
    && rm -Rf /usr/share/doc && rm -Rf /usr/share/man \
    && apt-get clean

# Install Ansible.
RUN apt-add-repository -y ppa:ansible/ansible \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       ansible \
    && rm -rf /var/lib/apt/lists/* \
    && rm -Rf /usr/share/doc && rm -Rf /usr/share/man \
    && apt-get clean

RUN useradd -m -s /bin/bash -u 1500 ubuntu \
    && echo "ubuntu     ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

COPY ./docker/entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]
CMD ["tail", "-f", "/dev/null" ]

USER ubuntu

COPY --chown=ubuntu:1500 ./tools /tmp/tools

RUN cd /tmp/tools \
    && touch ~/.s3cfg \
    && echo 'localhost' > hosts \
    && ansible-playbook -i hosts --connection=local site.yml \
    && ansible-playbook -i hosts --connection=local server-overlay.yml
