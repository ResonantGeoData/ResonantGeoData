resource "aws_route53_record" "watch" {
  name             = "_1665444c5f45134012652f2b83b63432.watch.resonantgeodata.com"
  type             = "CNAME"
  ttl              = "300"
  route53_zone_id  = aws_route53_zone.common.id
  records          = ["_4e20c5eb5edd4ea6f2b5f5c66ce76409.bbfvkzsszw.acm-validations.aws."]
}
