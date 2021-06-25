resource "aws_route53_record" "watch_acm_validation" {
  name    = "_1665444c5f45134012652f2b83b63432.watch.resonantgeodata.com"
  type    = "CNAME"
  ttl     = "300"
  zone_id = aws_route53_zone.common.id
  records = ["_4e20c5eb5edd4ea6f2b5f5c66ce76409.bbfvkzsszw.acm-validations.aws."]
}

resource "aws_route53_record" "watch" {
  name    = "watch.resonantgeodata.com"
  type    = "CNAME"
  ttl     = "300"
  zone_id = aws_route53_zone.common.zone_id
  records = ["rdg-elb2-955771211.us-west-2.elb.amazonaws.com."]
}

module "watch_smtp" {
  source  = "girder/girder/aws//modules/smtp"
  version = "0.8.0"

  fqdn            = aws_route53_record.watch.fqdn
  project_slug    = "watch"
  route53_zone_id = aws_route53_zone.common.zone_id
}

output "watch_smtp_url" {
  value     = "submission://${urlencode(module.watch_smtp.username)}:${urlencode(module.watch_smtp.password)}@${module.watch_smtp.host}:${module.watch_smtp.port}"
  sensitive = true
}
