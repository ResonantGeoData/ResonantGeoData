provider "aws" {
  alias               = "aws_ohio"
  region              = "us-east-2"
  allowed_account_ids = ["381864640041"]
  # Must set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY envvars
}

# Provisioned manually
data "aws_instance" "watch_dev" {
  provider = aws.aws_ohio

  filter {
    name   = "tag:Name"
    values = ["abhishek-rgd"]
  }
}

resource "aws_eip" "watch_dev" {
  provider = aws.aws_ohio

  instance = data.aws_instance.watch_dev.instance_id
  tags = {
    Name = "abhishek-rgd"
  }
}

resource "aws_route53_record" "watch_dev" {
  provider = aws.aws_ohio

  name    = "watch-test"
  type    = "A"
  zone_id = aws_route53_zone.common.zone_id
  records = [aws_eip.watch_dev.public_ip]
}
