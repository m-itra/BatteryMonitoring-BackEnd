param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$infrastructureDir = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $infrastructureDir ".env"

function Import-EnvFile {
    param(
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }

        $separatorIndex = $line.IndexOf("=")
        if ($separatorIndex -le 0) {
            return
        }

        $name = $line.Substring(0, $separatorIndex).Trim()
        $value = $line.Substring($separatorIndex + 1).Trim().Trim('"').Trim("'")

        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Hide-DatabasePassword {
    param(
        [string]$DatabaseUrl
    )

    if (-not $DatabaseUrl) {
        return ""
    }

    return $DatabaseUrl -replace "://([^:/@]+):([^@]+)@", '://$1:***@'
}

function Invoke-Checked {
    param(
        [string[]]$Command
    )

    & $Command[0] $Command[1..($Command.Length - 1)]
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $($Command -join ' ')"
    }
}

Import-EnvFile -Path $envPath

Push-Location $infrastructureDir

try {
    Write-Host "Ensuring local databases exist"
    Invoke-Checked @($Python, "scripts/ensure_databases.py")
    Write-Host "Running user-db migrations with USER_DATABASE_URL=$(Hide-DatabasePassword $env:USER_DATABASE_URL)"
    Invoke-Checked @($Python, "-m", "alembic", "-c", "migrations/user-db/alembic.ini", "upgrade", "head")
    Write-Host "Running battery-db migrations with BATTERY_DATABASE_URL=$(Hide-DatabasePassword $env:BATTERY_DATABASE_URL)"
    Invoke-Checked @($Python, "-m", "alembic", "-c", "migrations/battery-db/alembic.ini", "upgrade", "head")
}
finally {
    Pop-Location
}
