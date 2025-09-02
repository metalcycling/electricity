# Firewall

resource "aws_security_group" "firewall" {
  name        = "firewall"
  description = "Firewall traffic rules"

  tags = {
    Name = "firewall"
  }
}

resource "aws_vpc_security_group_ingress_rule" "ssh" {
  security_group_id = aws_security_group.firewall.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}

resource "aws_vpc_security_group_ingress_rule" "port-8080" {
  security_group_id = aws_security_group.firewall.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 8080
  ip_protocol       = "tcp"
  to_port           = 8080
}

resource "aws_vpc_security_group_ingress_rule" "port-80" {
  security_group_id = aws_security_group.firewall.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}

resource "aws_vpc_security_group_ingress_rule" "port-9090" {
  security_group_id = aws_security_group.firewall.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 9090
  ip_protocol       = "tcp"
  to_port           = 9090
}

resource "aws_vpc_security_group_ingress_rule" "port-3000" {
  security_group_id = aws_security_group.firewall.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 3000
  ip_protocol       = "tcp"
  to_port           = 3000
}

resource "aws_vpc_security_group_ingress_rule" "icmp" {
  security_group_id = aws_security_group.firewall.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = -1
  ip_protocol       = "icmp"
  to_port           = -1
}

resource "aws_vpc_security_group_egress_rule" "internet" {
  security_group_id = aws_security_group.firewall.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = -1
  ip_protocol       = "-1"
  to_port           = -1
}
