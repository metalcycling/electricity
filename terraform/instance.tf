# Instance

resource "aws_instance" "renard" {
  ami                    = "ami-0e1bed4f06a3b463d"
  instance_type          = "t2.micro"
  key_name               = "renard-ssh-key"
  vpc_security_group_ids = [aws_security_group.firewall.id]

  tags = {
    Name = "renard"
  }
}

output "renard_ip" {
  value = aws_instance.renard.public_ip
}
