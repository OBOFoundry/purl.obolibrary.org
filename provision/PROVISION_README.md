# Provision AWS instance.

## Requirements 

- The steps below were successfully tested using:
    - Terraform (0.14.4)

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
- In aws/vars.tf the private key and the public keys are assumed to be in the standard location

```
variable "public_key_path" {
  default = "~/.ssh/id_rsa.pub"
}

variable "private_key_path" {
  default = "~/.ssh/id_rsa"
}

```

#### AWS S3 Credentials

Prepare The s3 credential file needed for LogRotate. It should like so:

```sh
[default]
access_key = REPLACE_ME
secret_key = REPLACE_ME

```

#### Create AWS instance: 

Note: Terraform creates some folders and files to maintain the state. Use <i>ls -a aws</i>

```sh
cd provision

# This will install the aws provider. 
terraform -chdir=aws init

# Validate the config
terraform -chdir=aws validate

# View what is going to be created. The plan.
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
export PRIVATE_KEY=`terraform -chdir=aws output -raw private_key_path`

ssh -o StrictHostKeyChecking=no -i $PRIVATE_KEY ubuntu@$HOST
docker ps
which docker-compose
```

#### Stage To AWS Instance: 

Note: The ansible script assumes the S3 bucket credentials are in ~/.s3cfg 

```sh
cd provision
export HOST=`terraform -chdir=aws output -raw public_ip`
export PRIVATE_KEY=`terraform -chdir=aws output -raw private_key_path`
ansible-playbook -e "host=$HOST" --private-key $PRIVATE_KEY -u ubuntu -i "$HOST," stage.yaml
```

### Start Docker Instance: 

Start the instance and access it from broswer use http://REPLACE_WITH_ELASTIC_IP/

```
ssh -o StrictHostKeyChecking=no -i $PRIVATE_KEY ubuntu@$HOST
docker-compose -f docker-compose.yaml up -d

```

### Destroy AWS instance:
```
terraform -chdir=aws destroy
```


