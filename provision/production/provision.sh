#!/bin/bash
set -ex

ls -l aws/backend.tf production/purl-ssh production/purl-ssh.pub production/s3cfg > /dev/null
WORKSPACE=`terraform -chdir=aws workspace show`

if [ "$WORKSPACE" = "default" ]; then
   echo "default workspace should not be used. create a workspace production-yy-mm-dd"
   exit 1
fi

PROVISION_DIR=`pwd`
PUBLIC_KEY="$PROVISION_DIR/production/purl-ssh.pub"

printf 'tags = { Name = "purl-server", Workspace = "%s" }\n' $WORKSPACE > production/production-vars.tfvars
printf 'instance_type = "t2.micro"\n' >> production/production-vars.tfvars
printf 'disk_size = 16\n' >> production/production-vars.tfvars
printf 'public_key_path = "%s"\n' $PUBLIC_KEY >> production/production-vars.tfvars

cat $PROVISION_DIR/production/production-vars.tfvars

terraform -chdir=aws apply -auto-approve -var-file=$PROVISION_DIR/production/production-vars.tfvars

HOST=`terraform -chdir=aws output -raw public_ip`
PRIVATE_KEY=$PROVISION_DIR/production/purl-ssh
S3_CREDS=$PROVISION_DIR/production/s3cfg
STAGE_DIR=/home/ubuntu/stage_dir

ansible-playbook -e "stage_dir=$STAGE_DIR" -e "creds=$S3_CREDS" -u ubuntu -i "$HOST," --private-key $PRIVATE_KEY stage.yaml
ansible-playbook -e "stage_dir=$STAGE_DIR" -u ubuntu -i "$HOST," --private-key $PRIVATE_KEY start_services.yaml
