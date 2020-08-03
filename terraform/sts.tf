resource "aws_iam_role" "storage_upload" {
  name                 = "rgd-storage-upload-sts"
  max_session_duration = 12 * 60 * 60 # 12 hours
  assume_role_policy   = data.aws_iam_policy_document.storage_upload_assumeRolePolicy.json
}

data "aws_iam_policy_document" "storage_upload_assumeRolePolicy" {
  statement {
    principals {
      type = "AWS"
      identifiers = [
        module.django.iam_user.arn,
      ]
    }
    actions = [
      "sts:AssumeRole",
    ]
  }
}

resource "aws_iam_role_policy" "storage_upload" {
  name   = "rgd-storage-upload-sts"
  role   = aws_iam_role.storage_upload.name
  policy = data.aws_iam_policy_document.storage_upload.json
}

data "aws_iam_policy_document" "storage_upload" {
  statement {
    actions = [
      "s3:PutObject",
    ]
    resources = [
      "${module.django.storage_bucket.arn}/*",
    ]
  }
}
