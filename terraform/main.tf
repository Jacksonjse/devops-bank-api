provider "null" {}

resource "null_resource" "deploy" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = <<EOT
echo "Provisioning infra..."
ansible-playbook -i ../ansible/inventory.ini ../ansible/deploy.yml
EOT
  }
}