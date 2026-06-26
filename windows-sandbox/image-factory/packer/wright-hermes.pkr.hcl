packer {
  required_plugins {
    hyperv = {
      version = ">= 1.1.3"
      source  = "github.com/hashicorp/hyperv"
    }
  }
}

variable "iso_url" {
  type = string
}

variable "iso_checksum" {
  type = string
}

variable "autounattend_path" {
  type = string
}

variable "guest_username" {
  type    = string
  default = "wrightadmin"
}

variable "guest_password" {
  type      = string
  sensitive = true
}

variable "hermes_setup_url" {
  type = string
}

variable "hermes_setup_arguments" {
  type    = string
  default = "/S"
}

variable "hermes_install_timeout_seconds" {
  type    = number
  default = 600
}

variable "output_directory" {
  type = string
}

variable "vm_name" {
  type    = string
  default = "wright-hermes-image-build"
}

variable "switch_name" {
  type    = string
  default = "Default Switch"
}

source "hyperv-iso" "windows11" {
  boot_command         = []
  boot_wait            = "0s"
  communicator         = "winrm"
  cpus                 = 4
  disk_size            = 61440
  enable_secure_boot   = false
  enable_tpm           = true
  generation           = 2
  headless             = false
  iso_checksum         = var.iso_checksum
  iso_url              = var.iso_url
  memory               = 4096
  output_directory     = var.output_directory
  first_boot_device    = "DVD"
  shutdown_command     = "shutdown /s /t 10 /f /d p:4:1 /c \"Packer image shutdown\""
  switch_name          = var.switch_name
  vm_name              = var.vm_name
  winrm_password       = var.guest_password
  winrm_timeout        = "90m"
  winrm_username       = var.guest_username

  cd_files = [
    var.autounattend_path
  ]
  cd_label = "WRIGHT_ANSWER"
}

build {
  name    = "wright-hermes-ready"
  sources = ["source.hyperv-iso.windows11"]

  provisioner "powershell" {
    scripts = [
      "scripts/Install-BaseTools.ps1"
    ]
  }

  provisioner "powershell" {
    script            = "scripts/Install-HermesDesktop.ps1"
    environment_vars = [
      "HERMES_SETUP_URL=${var.hermes_setup_url}",
      "HERMES_SETUP_ARGUMENTS=${var.hermes_setup_arguments}",
      "HERMES_INSTALL_TIMEOUT_SECONDS=${var.hermes_install_timeout_seconds}"
    ]
  }

  provisioner "powershell" {
    scripts = [
      "scripts/Test-HermesReady.ps1"
    ]
  }
}
