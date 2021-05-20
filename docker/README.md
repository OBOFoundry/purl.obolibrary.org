## Using purl.obolibrary.org.git in docker

### Installation

- These steps were successfully tested on:
    - macOS (10.15.3)
    - Docker (19.03.5)

#### Prerequisites

The following tools should be available on the system.

- docker

#### AWS S3 Credentials

Prepare The s3 credential file used by logrotatePrepare. It should like so: 

```sh
[default]
access_key = REPLACE_ME
secret_key = REPLACE_ME
```

#### Clone the repository.

```sh
git clone https://github.com/OBOFoundry/purl.obolibrary.org.git
```

#### Build Purl Image.

```sh
cd purl.obolibrary.org
docker build -f docker/Dockerfile -t purl:latest .
docker image list | grep purl 
```

#### Launch Container.

Run interactively and access the web server using [http://localhost:8080](http://localhost:808).
Be sure to specify the absolute path to s3 credentials.

```sh
docker run --name purl -v REPLACE_ME:/opt/credentials/s3cfg -p 8080:80 -it purl:latest /bin/bash

sudo cat /opt/credentials/s3cfg   # Make sure crendetials were mounted properly
ps -ef                            # Make sure apache is running
```

#### Cleanup.

Stop Container.

```sh
docker stop purl
```

Delete Container.

```sh
docker rm -f purl
```

Delete Image.

```sh
docker image rm purl:latest
```

#### Test Inside Container.

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
