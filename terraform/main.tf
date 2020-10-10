terraform {
  backend "remote" {
    hostname     = "app.terraform.io"
    organization = "ResonantGeoData"

    workspaces {
      name = "ResonantGeoData"
    }
  }
}

provider "aws" {
  region              = "us-east-1"
  allowed_account_ids = ["381864640041"]
  # Must set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY envvars
}

provider "heroku" {
  # Must set HEROKU_EMAIL, HEROKU_API_KEY envvars
}

data "heroku_team" "common" {
  name = "resonantgeodata"
}

resource "aws_route53_zone" "common" {
  name = "resonantgeodata.com"
}

module "django" {
  source  = "girder/django/heroku"
  version = "0.5.0"

  project_slug     = "rgd"
  subdomain_name   = "www"
  heroku_team_name = data.heroku_team.common.name
  route53_zone_id  = aws_route53_zone.common.id

  # Optional overrides
  # See https://registry.terraform.io/modules/girder/django/heroku/
  # for other possible optional variables
  additional_django_vars = {
    SENTRY_DSN = "https://b3dac135af6c42fea439998200656ca3@o267860.ingest.sentry.io/5458973"
  }
  storage_bucket_name = "resonantgeodata-files"
  # This defaults to 1, but may be changed
  heroku_worker_dyno_quantity = 1
}
