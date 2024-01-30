#!/bin/bash
set -ex

INSTANCE_TYPE="t2.micro"
DISK_SIZE=16

ls -l aws/backend.tf production/purl-ssh production/purl-ssh.pub production/s3cfg > /dev/null
WORKSPACE=`terraform -chdir=aws workspace show`

if [ "$WORKSPACE" = "default" ]; then
   echo "default workspace should not be used. create a workspace production-yy-mm-dd"
   exit 1
fi

PROVISION_DIR=`pwd`
PUBLIC_KEY="$PROVISION_DIR/production/purl-ssh.pub"

printf 'tags = { Name = "purl-server", Workspace = "%s" }\n' $WORKSPACE > production/production-vars.tfvars
printf 'instance_type = "%s"\n' $INSTANCE_TYPE >> production/production-vars.tfvars
printf 'disk_size = %d\n' $DISK_SIZE >> production/production-vars.tfvars
printf 'public_key_path = "%s"\n' $PUBLIC_KEY >> production/production-vars.tfvars

cat $PROVISION_DIR/production/production-vars.tfvars
chmod 400 production/purl-ssh
chmod 400 production/purl-ssh.pub

diff -s <(ssh-keygen -l -f production/purl-ssh | cut -d' ' -f2) <(ssh-keygen -l -f production/purl-ssh.pub | cut -d' ' -f2)

terraform -chdir=aws apply -auto-approve -var-file=$PROVISION_DIR/production/production-vars.tfvars

HOST=`terraform -chdir=aws output -raw public_ip`
PRIVATE_KEY=$PROVISION_DIR/production/purl-ssh
S3_CREDS=$PROVISION_DIR/production/s3cfg
STAGE_DIR=/home/ubuntu/stage_dir

ansible-playbook -e "stage_dir=$STAGE_DIR" -e "creds=$S3_CREDS" -u ubuntu -i "$HOST," --private-key $PRIVATE_KEY stage.yaml
ansible-playbook -e "stage_dir=$STAGE_DIR" -u ubuntu -i "$HOST," --private-key $PRIVATE_KEY start_services.yaml
echo "Done"
