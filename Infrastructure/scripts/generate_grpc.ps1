param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$infrastructureDir = Split-Path -Parent $PSScriptRoot
$repositoryDir = Split-Path -Parent $infrastructureDir
$protoDir = Join-Path $infrastructureDir "protos"
$protoTargets = @(
    @{
        ProtoFile = "user_service.proto"
        TargetServices = @(
            "UserService",
            "ProcessingService",
            "AnalyticsService"
        )
    },
    @{
        ProtoFile = "battery_data_service.proto"
        TargetServices = @(
            "UserService",
            "ProcessingService"
        )
    }
)

function Invoke-Checked {
    param(
        [string[]]$Command
    )

    & $Command[0] $Command[1..($Command.Length - 1)]
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $($Command -join ' ')"
    }
}

function Set-CrlfLineEndings {
    param(
        [string]$Path
    )

    $content = [System.IO.File]::ReadAllText($Path)
    $content = $content -replace "`r?`n", "`r`n"
    $utf8NoBom = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($Path, $content, $utf8NoBom)
}

foreach ($protoTarget in $protoTargets) {
    $protoFilePath = Join-Path $protoDir $protoTarget.ProtoFile
    if (-not (Test-Path -LiteralPath $protoFilePath)) {
        throw "Proto file not found: $protoFilePath"
    }
}

$previousPythonWarnings = $env:PYTHONWARNINGS
$env:PYTHONWARNINGS = "ignore:pkg_resources is deprecated as an API:DeprecationWarning"

try {
    Invoke-Checked @($Python, "-c", "import grpc_tools.protoc")

    foreach ($protoTarget in $protoTargets) {
        $protoFilePath = Join-Path $protoDir $protoTarget.ProtoFile
        $protoBaseName = [System.IO.Path]::GetFileNameWithoutExtension($protoTarget.ProtoFile)

        foreach ($serviceName in $protoTarget.TargetServices) {
            $targetDir = Join-Path $repositoryDir $serviceName

            if (-not (Test-Path -LiteralPath $targetDir)) {
                throw "Target service directory not found: $targetDir"
            }

            Write-Host "Generating gRPC code from $($protoTarget.ProtoFile) for $serviceName"
            Invoke-Checked @(
                $Python,
                "-m",
                "grpc_tools.protoc",
                "-I",
                $protoDir,
                "--python_out=$targetDir",
                "--grpc_python_out=$targetDir",
                $protoFilePath
            )

            Set-CrlfLineEndings -Path (Join-Path $targetDir "$protoBaseName`_pb2.py")
            Set-CrlfLineEndings -Path (Join-Path $targetDir "$protoBaseName`_pb2_grpc.py")
        }
    }
}
finally {
    $env:PYTHONWARNINGS = $previousPythonWarnings
}

Write-Host "gRPC code generated from all proto files in $protoDir"
