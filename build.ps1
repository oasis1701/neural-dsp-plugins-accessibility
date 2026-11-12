# build.ps1 - packages addon\ into an installable .nvda-addon file in dist\.
# An NVDA add-on is a zip whose ROOT contains manifest.ini, so the archive is built from the
# contents of addon\ rather than from the folder itself.
param(
    [string]$OutDir = (Join-Path $PSScriptRoot 'dist')
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$addonDir = Join-Path $root 'addon'
$manifest = Join-Path $addonDir 'manifest.ini'
if (-not (Test-Path $manifest)) { throw "manifest.ini not found at $manifest" }

$name = 'neuralDspPluginsAccessibility'
$summary = $name
$version = '0.1.0'
foreach ($line in Get-Content $manifest) {
    if ($line -match '^\s*name\s*=\s*(.+?)\s*$') { $name = $Matches[1].Trim('"') }
    if ($line -match '^\s*version\s*=\s*(.+?)\s*$') { $version = $Matches[1].Trim('"') }
    if ($line -match '^\s*summary\s*=\s*(.+?)\s*$') { $summary = $Matches[1].Trim('"') }
}

# Render the markdown readme to the simple HTML file the manifest points at.
$mdPath = Join-Path $addonDir 'doc\en\readme.md'
$htmlPath = Join-Path $addonDir 'doc\en\readme.html'
if (Test-Path $mdPath) {
    $body = New-Object System.Text.StringBuilder
    $inList = $false
    foreach ($line in Get-Content $mdPath -Encoding UTF8) {
        $t = $line.TrimEnd()
        if ($t -match '^###\s+(.*)$') { if ($inList) { [void]$body.AppendLine('</ul>'); $inList = $false }; [void]$body.AppendLine("<h3>$($Matches[1])</h3>") }
        elseif ($t -match '^##\s+(.*)$') { if ($inList) { [void]$body.AppendLine('</ul>'); $inList = $false }; [void]$body.AppendLine("<h2>$($Matches[1])</h2>") }
        elseif ($t -match '^#\s+(.*)$') { if ($inList) { [void]$body.AppendLine('</ul>'); $inList = $false }; [void]$body.AppendLine("<h1>$($Matches[1])</h1>") }
        elseif ($t -match '^\s*-\s+(.*)$') {
            if (-not $inList) { [void]$body.AppendLine('<ul>'); $inList = $true }
            [void]$body.AppendLine("<li>$($Matches[1])</li>")
        }
        elseif ($t -eq '') { if ($inList) { [void]$body.AppendLine('</ul>'); $inList = $false } }
        else { if ($inList) { [void]$body.AppendLine('</ul>'); $inList = $false }; [void]$body.AppendLine("<p>$t</p>") }
    }
    if ($inList) { [void]$body.AppendLine('</ul>') }
    $html = @"
<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>$summary $version</title></head>
<body>
$($body.ToString())
</body></html>
"@
    # strip markdown emphasis markers that survived the simple conversion
    $html = $html -replace '\*\*([^*]+)\*\*', '<strong>$1</strong>'
    Set-Content -Path $htmlPath -Value $html -Encoding UTF8
    Write-Host "rendered $htmlPath"
}

if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir | Out-Null }
$addon = Join-Path $OutDir ("{0}-{1}.nvda-addon" -f $name, $version)
if (Test-Path $addon) { Remove-Item $addon -Force }

# Exclude __pycache__ so stale bytecode never ships.
$staging = Join-Path $env:TEMP ("neuralAccessBuild_" + [System.Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $staging | Out-Null
Copy-Item -Path (Join-Path $addonDir '*') -Destination $staging -Recurse -Force
Get-ChildItem -Path $staging -Recurse -Directory -Filter '__pycache__' | Remove-Item -Recurse -Force

# Written entry by entry rather than with Compress-Archive, which in Windows PowerShell 5.1
# stores paths with backslashes. A zip's paths use forward slashes.
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$stream = [System.IO.File]::Open($addon, [System.IO.FileMode]::Create)
$archive = New-Object System.IO.Compression.ZipArchive($stream, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    $prefix = (Resolve-Path $staging).Path.TrimEnd('\') + '\'
    foreach ($file in Get-ChildItem -Path $staging -Recurse -File) {
        $entryName = $file.FullName.Substring($prefix.Length).Replace('\', '/')
        [void][System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive, $file.FullName, $entryName, [System.IO.Compression.CompressionLevel]::Optimal)
    }
} finally {
    $archive.Dispose()
    $stream.Dispose()
}
Remove-Item $staging -Recurse -Force

Write-Host ("built {0}" -f $addon)
Get-Item $addon | Select-Object Name, Length, LastWriteTime | Format-List
