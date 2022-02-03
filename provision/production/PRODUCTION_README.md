# Production Testing

#### Using Browser

Use http://provided_ip_address

#### Access and Test AWS Instance: 

SSH into machine using provided elastic ip and ssh keys

Enter docker container.

```sh
docker exec -it purl /bin/bash
```

Check s3 config and services.

```sh
sudo cat /opt/credentials/s3cfg   # Make sure crendetials were mounted properly
ps -ef                            # Make sure apache and crond are running
```

Run tests and safe-update.

```sh
cd /var/www/purl.obolibrary.org
sudo make all test
sudo make safe-update
```

Test LogRotate. Use -f option to force log rotation.

```sh
sudo cat /opt/credentials/s3cfg
sudo logrotate -v -f /etc/logrotate.d/apache2
```
