# Builds the extension zip and (re)generates the repo index into docs/ (the
# GitHub Pages folder). With -Push it also commits and pushes, publishing the
# update. Re-run after bumping `version` in blender_manifest.toml.
#
#   powershell -ExecutionPolicy Bypass -File build_release.ps1
#   powershell -ExecutionPolicy Bypass -File build_release.ps1 -Push
#   ... -Blender "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"

param(
    [string]$Blender = "blender",           # blender.exe (on PATH or full path)
    [string]$Repo    = "$PSScriptRoot\docs", # GitHub Pages folder (served root)
    [switch]$Push                            # commit + push docs/ after building
)

$ErrorActionPreference = "Stop"
$src = $PSScriptRoot

# Resolve Blender if the default isn't on PATH.
if (-not (Get-Command $Blender -ErrorAction SilentlyContinue)) {
    $guess = Get-ChildItem "C:\Program Files\Blender Foundation" -Filter blender.exe `
             -Recurse -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
    if ($guess) { $Blender = $guess.FullName }
    else { throw "Blender not found. Pass -Blender <path to blender.exe>." }
}

# Read version from the manifest for a tidy commit message.
$verLine = Select-String -Path "$src\blender_manifest.toml" -Pattern '^\s*version\s*=\s*"(.+)"'
$version = if ($verLine) { $verLine.Matches[0].Groups[1].Value } else { "?" }

New-Item -ItemType Directory -Force -Path $Repo | Out-Null

Write-Host "==> Validating..." -ForegroundColor Cyan
& $Blender --command extension validate $src
if ($LASTEXITCODE -ne 0) { throw "Validation failed." }

Write-Host "==> Building zip -> docs/ ..." -ForegroundColor Cyan
& $Blender --command extension build --source-dir $src --output-dir $Repo
if ($LASTEXITCODE -ne 0) { throw "Build failed." }

Write-Host "==> Generating repository index..." -ForegroundColor Cyan
& $Blender --command extension server-generate --repo-dir $Repo
if ($LASTEXITCODE -ne 0) { throw "server-generate failed." }

Get-ChildItem $Repo | Select-Object Name, Length | Format-Table -AutoSize

if ($Push) {
    Write-Host "==> Publishing v$version to GitHub..." -ForegroundColor Cyan
    git -C $src add docs
    git -C $src commit -m "Release v$version"
    git -C $src push
    Write-Host "Pushed. Blender will offer the update on its next check." -ForegroundColor Green
} else {
    Write-Host "`nBuilt v$version. Run with -Push to publish, or commit docs/ yourself." -ForegroundColor Green
}
