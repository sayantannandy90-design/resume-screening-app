# Resume Screening App (Azure)

A cloud-based resume analyzer using:
- Azure Document Intelligence
- Azure Blob Storage
- Azure Container Apps

## Quick Start

- Build + push image from repo using ACR Quick Task
- Deploy to Container Apps
- Configure environment variables:
  - FR_ENDPOINT
  - FR_KEY
  - STORAGE_CONNECTION
  - STORAGE_CONTAINER (default = resumes)
