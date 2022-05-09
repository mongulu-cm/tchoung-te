provider "aws" {
  region = var.region
}

terraform {
  # required_version = ">= 1.0"

  backend "s3" {
    bucket = "terraform-state-mongulu"
    key    = "tchoung-te/terraform.tfstate"
    region = "eu-central-1"
    //encrypt = true
  }
}
