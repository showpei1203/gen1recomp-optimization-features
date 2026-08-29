param(
    [string]$Workspace = "$env:USERPROFILE\SoulGoldRecomp_S0",
    [switch]$BuildSoulGold
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$SoulGoldRepo = 'https://github.com/Eemeliri/soulgold.git'
$SoulGoldCommit = 'a6efa38348f978348da9dc4f4a7878cccf27bfd0'
$GbaRecompRepo = 'https://github.com/mstan/gbarecomp.git'
$GbaRecompCommit = 'ed9824b70aa350cd9e1653894beaf6b1b6b27787'
$EmeraldRecompRepo = 'https://github.com/mstan/EmeraldRecomp.git'
$EmeraldRecompCommit = '4e1f89669b9945e338c0f2e52816aa0533fa30d3'

$LogDir = Join-Path $Workspace '_evidence'
$LogPath = Join-Path $LogDir ('S0_BOOTSTRAP_{0}.log' -f (Get-Date -Format 'yyyyMMdd_HHmmss'))

New-Item -ItemType Directory -Force -Path $Workspace | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log([string]$Message) {
    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Message
    $line | Tee-Object -FilePath $LogPath -Append
}

function Require-Command([string]$Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) { throw "Required command not found: $Name" }
    Write-Log "FOUND $Name -> $($cmd.Source)"
}

function Clone-Pinned([string]$Name, [string]$Url, [string]$Commit) {
    $dest = Join-Path $Workspace $Name
    if (-not (Test-Path (Join-Path $dest '.git'))) {
        Write-Log "CLONE $Url -> $dest"
        git clone --filter=blob:none $Url $dest 2>&1 | Tee-Object -FilePath $LogPath -Append
    } else {
        Write-Log "EXISTS $dest; fetching target commit"
        git -C $dest fetch origin $Commit 2>&1 | Tee-Object -FilePath $LogPath -Append
    }

    git -C $dest checkout --detach $Commit 2>&1 | Tee-Object -FilePath $LogPath -Append
    $head = (git -C $dest rev-parse HEAD).Trim()
    if ($head -ne $Commit) { throw "$Name pin mismatch: expected $Commit got $head" }
    Write-Log "PIN_OK $Name $head"
    return $dest
}

function Get-FileHashes([string]$Path) {
    if (-not (Test-Path $Path)) { return $null }
    $fi = Get-Item $Path
    $sha1 = (Get-FileHash $Path -Algorithm SHA1).Hash.ToLowerInvariant()
    $sha256 = (Get-FileHash $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    return [pscustomobject]@{
        Path = $fi.FullName
        Size = $fi.Length
        SHA1 = $sha1
        SHA256 = $sha256
    }
}

try {
    Write-Log 'SoulGold Recomp S0 bootstrap start'
    Write-Log "WORKSPACE $Workspace"
    Require-Command git

    $sg = Clone-Pinned 'soulgold' $SoulGoldRepo $SoulGoldCommit
    $gb = Clone-Pinned 'gbarecomp' $GbaRecompRepo $GbaRecompCommit
    $er = Clone-Pinned 'EmeraldRecomp' $EmeraldRecompRepo $EmeraldRecompCommit

    Write-Log 'UPSTREAM_PINS_OK=1'

    $wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
    if ($wsl) {
        Write-Log "FOUND wsl.exe -> $($wsl.Source)"
        try {
            $wslInfo = (& wsl.exe bash -lc 'printf "WSL_OK=1\n"; uname -a; command -v make || true; command -v arm-none-eabi-gcc || true; command -v python3 || true' 2>&1) -join "`n"
            $wslInfo | Tee-Object -FilePath $LogPath -Append
        } catch {
            Write-Log "WSL_PROBE_FAIL $($_.Exception.Message)"
        }
    } else {
        Write-Log 'WSL_FOUND=0'
    }

    if ($BuildSoulGold) {
        if (-not $wsl) { throw 'BuildSoulGold requested but WSL is unavailable.' }
        $sgWin = (Resolve-Path $sg).Path
        $sgWsl = (& wsl.exe wslpath -a $sgWin).Trim()
        if (-not $sgWsl) { throw 'Unable to translate SoulGold workspace path into WSL path.' }

        Write-Log "SOULGOLD_BUILD_START $sgWsl"
        $buildCmd = "set -o pipefail; cd '$sgWsl'; make -j\$(nproc) 2>&1 | tee '$sgWsl/S0_SOULGOLD_BUILD.log'"
        & wsl.exe bash -lc $buildCmd
        if ($LASTEXITCODE -ne 0) { throw "SoulGold make failed with exit code $LASTEXITCODE" }
        Write-Log 'SOULGOLD_BUILD_EXIT=0'
    }

    $expected = @(
        'Soulgold_Beta_1.gba',
        'Soulgold_Beta_1.elf',
        'Soulgold_Beta_1.map',
        'Soulgold_Beta_1.sym'
    )

    $authority = @()
    foreach ($name in $expected) {
        $p = Join-Path $sg $name
        $h = Get-FileHashes $p
        if ($h) {
            Write-Log "ARTIFACT_FOUND $name size=$($h.Size) sha1=$($h.SHA1) sha256=$($h.SHA256)"
            $authority += $h
        } else {
            Write-Log "ARTIFACT_MISSING $name"
        }
    }

    $jsonPath = Join-Path $LogDir 'S0_SOURCE_AUTHORITY.json'
    [pscustomobject]@{
        captured_at = (Get-Date).ToString('o')
        workspace = $Workspace
        pins = [ordered]@{
            soulgold = $SoulGoldCommit
            gbarecomp = $GbaRecompCommit
            emeraldrecomp = $EmeraldRecompCommit
        }
        artifacts = $authority
    } | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 $jsonPath

    Write-Log "AUTHORITY_JSON $jsonPath"
    Write-Log 'RESULT=PASS'
}
catch {
    Write-Log "RESULT=FAIL"
    Write-Log "ERROR=$($_.Exception.Message)"
    Write-Host ''
    Write-Host "Bootstrap failed. Return this log: $LogPath" -ForegroundColor Red
    Read-Host 'Press Enter to close'
    exit 1
}

Write-Host ''
Write-Host 'S0 bootstrap completed.' -ForegroundColor Green
Write-Host "Evidence: $LogDir"
if (-not $BuildSoulGold) {
    Write-Host 'Upstreams are pinned. Re-run with -BuildSoulGold when the WSL ARM toolchain is ready.'
}
Read-Host 'Press Enter to close'
