# Provision AWS Instance

## Requirements 

- The steps below were successfully tested using:
    - Terraform (v1.1.4)
    - Ansible   (2.10.7) Python (3.8.5)

#### Install Terraform

- Go to [url](https://learn.hashicorp.com/tutorials/terraform/install-cli)

#### AWS Credentials.
- Create a file or override the location in aws/provider.tf

```
[default]
aws_access_key_id = XXXX
aws_secret_access_key = XXXX
```
#### SSH Credentials.
- In aws/vars.tf the public key is assumed to be in the standard location

```
variable "public_key_path" {
  default = "~/.ssh/id_rsa.pub"
}

```

#### AWS S3 Credentials

Prepare The s3 credential file needed for LogRotate. It should like so:

```sh
[default]
access_key = REPLACE_ME
secret_key = REPLACE_ME
```

#### Create AWS instance: with an Elstaic ip 

Note: Terraform creates some folders and files to maintain the state. 
      Once terraform is applied, you can see them using <i>ls -a aws</i>

```sh
cd provision

# This will install the aws provider. 
terraform -chdir=aws init

# Validate the terraform scripts' syntax
terraform -chdir=aws validate

# View the plan that is going to be created.
# This is very useful as it will also search for the elastic ip using 
# the supplied eip_alloc_id. And would fail if it does not find it.
terraform -chdir=aws plan

# This will create the vpc, security group and the instance
terraform -chdir=aws apply

# To view the outputs
terraform -chdir=aws output 

#To view what was deployed:
terraform -chdir=aws show 
```

#### Test AWS Instance: 

```sh
export HOST=`terraform -chdir=aws output -raw public_ip`
export PRIVATE_KEY=YOUR_PRIVATE_KEY_PATH

ssh -o StrictHostKeyChecking=no -i $PRIVATE_KEY ubuntu@$HOST
docker ps
which docker-compose
```

#### Stage To AWS Instance: 

Clone the repo on the AWS instance, build the docker image and finally copy 
the s3config and the docker-compose file. 

Note: The ansible script assumes the S3 bucket credentials are in ~/.s3cfg 

```sh
cd provision
export HOST=`terraform -chdir=aws output -raw public_ip`
export PRIVATE_KEY=YOUR_PRIVATE_KEY_PATH

ansible-playbook -e "host=$HOST" -u ubuntu --private-key $PRIVATE_KEY -i "$HOST," stage.yaml
ansible-playbook -e "host=$HOST" -u ubuntu --private-key $PRIVATE_KEY -i "$HOST," start_services.yaml

# down services
ansible-playbook -e "host=$HOST" -u ubuntu --private-key $PRIVATE_KEY -i "$HOST," down_services.yaml
```

#### Start Docker Instance Manually: 

Start the instance and access it from browser use http://REPLACE_WITH_ELASTIC_IP/

```
ssh -o StrictHostKeyChecking=no -i $PRIVATE_KEY ubuntu@$HOST
docker-compose -f docker-compose.yaml up -d
```

#### Testing Inside Container

Enter container.

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

#### Destroy AWS instance:

Destroy when done.

Note: The terraform state is stored in the directory aws. 
      Do not lose it or delete it

```
terraform -chdir=aws destroy
```


