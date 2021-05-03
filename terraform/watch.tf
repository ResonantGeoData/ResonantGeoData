resource "aws_route53_record" "watch" {
  name    = "_1665444c5f45134012652f2b83b63432.watch.resonantgeodata.com"
  type    = "CNAME"
  ttl     = "300"
  zone_id = aws_route53_zone.common.id
  records = ["_4e20c5eb5edd4ea6f2b5f5c66ce76409.bbfvkzsszw.acm-validations.aws."]
}

resource "aws_route53_record" "www-watch" {
  zone_id = aws_route53_zone.common.zone_id
  name    = "watch.resonantgeodata.com"
  type    = "A"

  alias {
    name                   = "RDG-ELB1-758710195.us-west-2.elb.amazonaws.com"
    zone_id                = "Z1H1FL5HABSF5"
    evaluate_target_health = true
  }
}
