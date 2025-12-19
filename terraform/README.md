# hw3-IoC
## files
`main.tf` config of terraform
`variables.tf` definition of variables
`terraform.tfvars` value of variables
## deploy commands
fill the value of enviorment variables in `terraform.tfvars`
```cmd
cd terraform

terraform plan -var-file terraform.tfvars

# for the first time
terraform init

# check the changes
terraform plan -var-file=terraform.tfvars

# deploy command
terraform apply -var-file=terraform.tfvars
```