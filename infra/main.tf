locals {
  domain_name = "tchoung-te.mongulu.cm"
}

resource "aws_cloudfront_distribution" "cf" {
  aliases = [local.domain_name]
  comment = "Managed by Terraform"

  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cache_policy_id        = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    cached_methods         = ["GET", "HEAD"]
    compress               = "true"
    default_ttl            = "0"
    max_ttl                = "0"
    min_ttl                = "0"
    smooth_streaming       = "false"
    target_origin_id       = "mongulu-prod-tchoun-te"
    viewer_protocol_policy = "redirect-to-https"
  }

  enabled         = "true"
  http_version    = "http2"
  is_ipv6_enabled = "true"

  origin {
    connection_attempts = "3"
    connection_timeout  = "10"

    custom_origin_config {
      http_port                = "80"
      https_port               = "443"
      origin_keepalive_timeout = "5"
      origin_protocol_policy   = "https-only"
      origin_read_timeout      = "30"
      origin_ssl_protocols     = ["TLSv1", "TLSv1.1", "TLSv1.2"]
    }

    domain_name = "mongulu.gogocarto.fr"
    origin_id   = "mongulu-prod-tchoun-te"
  }

  price_class = "PriceClass_100"

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  retain_on_delete = "false"

  tags = {
    Name      = "mongulu-prod-tchoun-te"
    Namespace = "mongulu"
    Stage     = "prod"
  }

  tags_all = {
    Name      = "mongulu-prod-tchoun-te"
    Namespace = "mongulu"
    Stage     = "prod"
  }

  viewer_certificate {
    acm_certificate_arn            = "arn:aws:acm:us-east-1:053932140667:certificate/35f51ab4-1f12-4a13-a96a-b590bbc80b7a"
    cloudfront_default_certificate = "false"
    minimum_protocol_version       = "TLSv1.2_2019"
    ssl_support_method             = "sni-only"
  }
}

resource "aws_route53_record" "tchoung-te-route" {
  name    = local.domain_name
  records = [aws_cloudfront_distribution.cf.domain_name]
  ttl     = "300"
  type    = "CNAME"
  zone_id = "Z08957171V7QJR4XM6QTY"
}
