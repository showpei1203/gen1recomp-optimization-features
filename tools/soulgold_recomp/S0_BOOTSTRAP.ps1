param(
    [string]$Workspace = "$env:USERPROFILE\SoulGoldRecomp_S0",
    [switch]$BuildSoulGold,
    [switch]$NoPause
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
    Add-Content -Path $LogPath -Value $line -Encoding UTF8
    Write-Host $line
}

function To-WslPath([string]$Path) {
    $value = @(& wsl.exe wslpath -a $Path 2>&1)
    if ($LASTEXITCODE -ne 0) { throw "wslpath failed for $Path" }
    return ($value | Select-Object -Last 1).Trim()
}

$WinGit = Get-Command git.exe -ErrorAction SilentlyContinue
$Wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue

function Invoke-WindowsGit([string[]]$GitArgs) {
    $lines = @(& git.exe @GitArgs 2>&1)
    $rc = $LASTEXITCODE
    foreach ($line in $lines) { Write-Log "GIT[WIN] $line" }
    if ($rc -ne 0) { throw "git failed ($rc): git $($GitArgs -join ' ')" }
}

function Invoke-WslGit([string[]]$GitArgs) {
    $lines = @(& wsl.exe git @GitArgs 2>&1)
    $rc = $LASTEXITCODE
    foreach ($line in $lines) { Write-Log "GIT[WSL] $line" }
    if ($rc -ne 0) { throw "WSL git failed ($rc): git $($GitArgs -join ' ')" }
}

function Clone-Pinned([string]$Name, [string]$Url, [string]$Commit) {
    $dest = Join-Path $Workspace $Name

    if ($WinGit) {
        if (-not (Test-Path (Join-Path $dest '.git'))) {
            Write-Log "CLONE[WIN] $Url -> $dest"
            Invoke-WindowsGit @('clone', '--filter=blob:none', $Url, $dest)
        } else {
            Write-Log "EXISTS[WIN] $dest; fetching target commit"
            Invoke-WindowsGit @('-C', $dest, 'fetch', 'origin', $Commit)
        }
        Invoke-WindowsGit @('-C', $dest, 'checkout', '--detach', $Commit)
        $head = (& git.exe -C $dest rev-parse HEAD).Trim()
        if ($LASTEXITCODE -ne 0) { throw "Unable to read $Name HEAD" }
    } else {
        if (-not $Wsl) { throw 'Neither Git for Windows nor WSL is available.' }
        $destWsl = To-WslPath $dest
        if (-not (Test-Path (Join-Path $dest '.git'))) {
            Write-Log "CLONE[WSL] $Url -> $destWsl"
            Invoke-WslGit @('clone', '--filter=blob:none', $Url, $destWsl)
        } else {
            Write-Log "EXISTS[WSL] $destWsl; fetching target commit"
            Invoke-WslGit @('-C', $destWsl, 'fetch', 'origin', $Commit)
        }
        Invoke-WslGit @('-C', $destWsl, 'checkout', '--detach', $Commit)
        $headLines = @(& wsl.exe git -C $destWsl rev-parse HEAD 2>&1)
        if ($LASTEXITCODE -ne 0) { throw "Unable to read $Name HEAD through WSL git" }
        $head = ($headLines | Select-Object -Last 1).Trim()
    }

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

    if ($WinGit) {
        Write-Log "GIT_BACKEND=WINDOWS $($WinGit.Source)"
    } elseif ($Wsl) {
        $gitProbe = @(& wsl.exe git --version 2>&1)
        if ($LASTEXITCODE -ne 0) { throw 'Git is missing inside WSL.' }
        Write-Log ("GIT_BACKEND=WSL " + (($gitProbe | Select-Object -First 1).ToString()))
    } else {
        throw 'Git unavailable: install WSL or Git for Windows.'
    }

    $sg = Clone-Pinned 'soulgold' $SoulGoldRepo $SoulGoldCommit
    $gb = Clone-Pinned 'gbarecomp' $GbaRecompRepo $GbaRecompCommit
    $er = Clone-Pinned 'EmeraldRecomp' $EmeraldRecompRepo $EmeraldRecompCommit

    Write-Log 'UPSTREAM_PINS_OK=1'

    if ($BuildSoulGold) {
        if (-not $Wsl) { throw 'BuildSoulGold requested but WSL is unavailable.' }
        $sgWin = (Resolve-Path $sg).Path
        $sgWsl = To-WslPath $sgWin
        if (-not $sgWsl) { throw 'Unable to translate SoulGold workspace path into WSL path.' }

        $nprocLines = @(& wsl.exe nproc 2>&1)
        if ($LASTEXITCODE -ne 0) { throw 'Unable to query WSL CPU count with nproc.' }
        $jobs = (($nprocLines | Select-Object -Last 1).ToString()).Trim()
        if ($jobs -notmatch '^\d+$') { $jobs = '4' }

        Write-Log "SOULGOLD_BUILD_START $sgWsl jobs=$jobs"
        $buildLines = @(& wsl.exe make -C $sgWsl "-j$jobs" 2>&1)
        $buildRc = $LASTEXITCODE
        foreach ($line in $buildLines) { Write-Log "MAKE $line" }
        if ($buildRc -ne 0) { throw "SoulGold make failed with exit code $buildRc" }
        Write-Log 'SOULGOLD_BUILD_EXIT=0'
    }

    $expected = @(
        'Soulgold_Beta_1.gba',
        'Soulgold_Beta_1.elf',
        'Soulgold_Beta_1.map',
        'Soulgold_Beta_1.sym'
    )

    $authority = @()
    $missingArtifacts = @()
    foreach ($name in $expected) {
        $p = Join-Path $sg $name
        $h = Get-FileHashes $p
        if ($h) {
            Write-Log "ARTIFACT_FOUND $name size=$($h.Size) sha1=$($h.SHA1) sha256=$($h.SHA256)"
            $authority += $h
        } else {
            Write-Log "ARTIFACT_MISSING $name"
            $missingArtifacts += $name
        }
    }
    if ($BuildSoulGold -and $missingArtifacts.Count -gt 0) {
        throw "SoulGold build exited successfully but required outputs are missing: $($missingArtifacts -join ', ')"
    }

    $jsonPath = Join-Path $LogDir 'S0_SOURCE_AUTHORITY.json'
    [pscustomobject]@{
        captured_at = (Get-Date).ToString('o')
        workspace = $Workspace
        git_backend = $(if ($WinGit) { 'windows' } else { 'wsl' })
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
    Write-Log 'RESULT=FAIL'
    Write-Log "ERROR=$($_.Exception.Message)"
    Write-Host ''
    Write-Host "Bootstrap failed. Return this log: $LogPath" -ForegroundColor Red
    if (-not $NoPause) { Read-Host 'Press Enter to close' }
    exit 1
}

Write-Host ''
Write-Host 'S0 bootstrap completed.' -ForegroundColor Green
Write-Host "Evidence: $LogDir"
if (-not $BuildSoulGold) {
    Write-Host 'Upstreams are pinned. Re-run with -BuildSoulGold when the WSL ARM toolchain is ready.'
}
if (-not $NoPause) { Read-Host 'Press Enter to close' }
