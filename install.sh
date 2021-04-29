#!/bin/sh

DOMAIN="purl.obolibrary.org"
DIR="/var/www/${DOMAIN}"

# Install packages
apt-get update || exit 1
apt-get install -y \
   apache2 \
   git \
   python3 \
   python3-pip \
   || exit 1
pip3 install -r requirements.txt || exit 1

# Apache2 configuration file
cat << EOF > /etc/apache2/sites-available/${DOMAIN}.conf
<VirtualHost *:80>
    ServerName ${DOMAIN}

    # Root directory:
    # the only Option is FollowSymLinks (not ExecCGI, Includes, Indexes)
    # the only AllowOverride is FileInfo (not Options)
    # see https://httpd.apache.org/docs/current/mod/core.html#allowoverride
    DocumentRoot ${DIR}/www
    <Directory ${DIR}/www>
      AllowOverride FileInfo
      Options FollowSymLinks
      Order allow,deny
      Allow from all
    </Directory>

    # Custom access log in "Common Log Format (CLF)" plus Referer, User-agent, and Location
    # See http://httpd.apache.org/docs/2.4/mod/mod_log_config.html
    CustomLog /var/log/apache2/${DOMAIN}.access.log "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\" \"%{Location}o\""
    ErrorLog /var/log/apache2/${DOMAIN}.error.log
</VirtualHost>
EOF

# Disable default site
a2dissite 000-default

# Enable PURL site
a2ensite ${DOMAIN}.conf

# Restart Apache2
service apache2 enable
service apache2 restart
