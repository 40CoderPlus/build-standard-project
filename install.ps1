[CmdletBinding()]
param(
    [string]$InstallRoot = $env:CODEX_HOME
)

$ErrorActionPreference = 'Stop'

$source = Join-Path $PSScriptRoot 'skills\build-standard-project'
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md') -PathType Leaf)) {
    throw "Invalid release: SKILL.md is missing from $source"
}

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    $InstallRoot = Join-Path $env:USERPROFILE '.codex'
}

$skillsDirectory = [IO.Path]::GetFullPath((Join-Path $InstallRoot 'skills'))
$target = [IO.Path]::GetFullPath((Join-Path $skillsDirectory 'build-standard-project'))
if (-not $target.StartsWith($skillsDirectory + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing installation target outside the Codex skills directory: $target"
}

New-Item -ItemType Directory -Path $skillsDirectory -Force | Out-Null

$backup = $null
if (Test-Path -LiteralPath $target) {
    $timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backup = "$target.backup-$timestamp"
    Move-Item -LiteralPath $target -Destination $backup
}

try {
    Copy-Item -LiteralPath $source -Destination $target -Recurse
}
catch {
    if ($backup -and -not (Test-Path -LiteralPath $target) -and (Test-Path -LiteralPath $backup)) {
        Move-Item -LiteralPath $backup -Destination $target
    }
    throw
}

Write-Host "Installed build-standard-project 1.6.0 to $target"
if ($backup) {
    Write-Host "Previous installation backed up to $backup"
}
Write-Host 'The Skill will be available from the next Codex conversation.'
