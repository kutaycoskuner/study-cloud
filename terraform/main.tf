# The first Terraform configuration: one container from the app image.
# Run from this folder: terraform init, terraform plan, terraform apply

# 1. Which providers this configuration needs, and from where
terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"   # the Docker provider, from the Terraform Registry
      version = "~> 3.0"               # any 3.x version, not 4.0
    }
  }
}

# 2. How to reach Docker: Docker Desktop on Windows listens on this named pipe
provider "docker" {
  host = "npipe:////./pipe/docker_engine"
}

# 3. The image: already built locally, so Terraform only looks it up
resource "docker_image" "app" {
  name         = "study-cloud:dev"
  keep_locally = true                  # on destroy, keep the image (it isn't Terraform's to delete)
}

# 4. The container, created from that image
resource "docker_container" "app" {
  name  = "study-cloud-tf"
  image = docker_image.app.image_id    # a reference: Terraform creates the image resource first

  ports {
    internal = 8000                    # the app's port inside the container
    external = 8080                    # on your laptop: http://127.0.0.1:8080
  }
}
