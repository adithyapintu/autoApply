param(
  [switch]$Build,
  [switch]$GenSecrets
)

# Generate strong random secrets if still at defaults
if ($GenSecrets -or (Select-String -Path ".env" -Pattern "change-me-access" -Quiet)) {
  Write-Host "⚙  Generating secrets..." -ForegroundColor Cyan
  $access  = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
  $refresh = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
  $pepper  = [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
  (Get-Content .env) `
    -replace "JWT_ACCESS_SECRET=.*",  "JWT_ACCESS_SECRET=$access" `
    -replace "JWT_REFRESH_SECRET=.*", "JWT_REFRESH_SECRET=$refresh" `
    -replace "PASSWORD_PEPPER=.*",    "PASSWORD_PEPPER=$pepper" |
    Set-Content .env
  Write-Host "✓  Secrets written to .env" -ForegroundColor Green
}

if ($Build) {
  docker compose up --build
} else {
  docker compose up
}

