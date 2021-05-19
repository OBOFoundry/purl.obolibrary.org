## Using purl.obolibrary.org.git in docker

### Installation

- These steps were successfully tested on:
    - macOS (10.15.3)

#### Prerequisites

The following tools should be available on the system.

- docker

####  

Clone the repository.

```sh
git clone https://github.com/OBOFoundry/purl.obolibrary.org.git
```

#### Build Purl Image.

From the root directory of the repository, install the dependencies in a Conda environment called `sciencecapsule`:

```sh
cd purl.obolibrary.org
docker build -f docker/Dockerfile -t purl .
```

#### Run Container.

Run interactively. 

```sh
docker run --name purl -v path_to_s3_config:/opt/credentials/s3cfg -p 8080:80 -it purl /bin/bash
```

Stop container.

```sh
docker stop purl
```

Delete container.

```sh
docker rm -f purl
```
