param(
  [Parameter(Mandatory=$true)]
  [string]$ZipPath
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$ZipPath = (Resolve-Path $ZipPath).Path
$baseDir = Split-Path $ZipPath -Parent
$stem = [System.IO.Path]::GetFileNameWithoutExtension($ZipPath)
$outZip = Join-Path $baseDir ($stem + "_LOCALIZATION_SOURCE.zip")
$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("rmxp_zh_tw_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $temp | Out-Null

function Normalize-Entry([string]$name) {
  return ($name -replace "\\","/").TrimStart("/")
}

function Should-Include([string]$name) {
  $n = Normalize-Entry $name
  if ($n -match '(^|/)(Data|PBS|Plugins|Fonts|Text_[^/]+)(/|$)') { return $true }
  if ($n -match '(^|/)Graphics/Fonts(/|$)') { return $true }

  $leaf = [System.IO.Path]::GetFileName($n)
  if ($leaf -match '^(Game\.ini|Game\.rxproj|mkxp.*\.json|version.*\.txt|intl\.txt|language.*\.txt|languages.*\.txt)$') { return $true }
  if ($n -notmatch '/' -and $leaf -match '\.(rb|txt|ini|json|cfg)$') { return $true }
  return $false
}

$archive = [System.IO.Compression.ZipFile]::OpenRead($ZipPath)
$included = New-Object System.Collections.Generic.List[string]
try {
  foreach ($entry in $archive.Entries) {
    if ([string]::IsNullOrEmpty($entry.Name)) { continue }
    if (-not (Should-Include $entry.FullName)) { continue }
    $rel = Normalize-Entry $entry.FullName
    $dest = Join-Path $temp ($rel -replace '/', [System.IO.Path]::DirectorySeparatorChar)
    $destDir = Split-Path $dest -Parent
    if (-not (Test-Path $destDir)) { New-Item -ItemType Directory -Force -Path $destDir | Out-Null }
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $dest, $true)
    $included.Add($rel) | Out-Null
  }
}
finally { $archive.Dispose() }

$hash = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLowerInvariant()
$manifest = @(
  "RMXP Pokemon zh-TW localization source pack",
  "Created: $([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))",
  "Original ZIP: $([System.IO.Path]::GetFileName($ZipPath))",
  "Original size: $((Get-Item $ZipPath).Length) bytes",
  "Original SHA256: $hash",
  "Included files: $($included.Count)",
  "",
  "Included paths:",
  ($included | Sort-Object)
)
$manifest | Set-Content -Encoding UTF8 (Join-Path $temp "LOCALIZATION_SOURCE_MANIFEST.txt")

if (Test-Path $outZip) { Remove-Item $outZip -Force }
[System.IO.Compression.ZipFile]::CreateFromDirectory($temp,$outZip,[System.IO.Compression.CompressionLevel]::Optimal,$false)
Remove-Item $temp -Recurse -Force

$size = (Get-Item $outZip).Length
Write-Host ""
Write-Host "Created: $outZip"
Write-Host "Size: $size bytes"
Write-Host "Files included: $($included.Count)"
Write-Host ""
if ($size -gt 250MB) {
  Write-Warning "The localization source pack is still over 250 MB. Upload it anyway; the filter can be tightened further if needed."
} else {
  Write-Host "This pack is under the 250 MB connector threshold."
}
