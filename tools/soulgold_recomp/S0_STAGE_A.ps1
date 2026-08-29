param(
    [string]$Workspace = "$env:USERPROFILE\SoulGoldRecomp_S0"
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Evidence = Join-Path $Workspace '_evidence'
New-Item -ItemType Directory -Force -Path $Evidence | Out-Null
$Log = Join-Path $Evidence ('S0_STAGE_A_{0}.log' -f (Get-Date -Format 'yyyyMMdd_HHmmss'))

function Log([string]$s) {
    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $s
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Host $line
}

function WslPath([string]$p) {
    $resolved = (Resolve-Path $p).Path
    $value = @(& wsl.exe wslpath -a $resolved 2>&1)
    if ($LASTEXITCODE -ne 0) { throw "wslpath failed for $resolved" }
    return ($value | Select-Object -Last 1).Trim()
}

try {
    Log 'S0_STAGE_A_BEGIN'
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
        throw 'WSL is required for the pinned SoulGold build. WSL2 is the upstream-recommended Windows path.'
    }

    $winGit = Get-Command git.exe -ErrorAction SilentlyContinue
    if ($winGit) {
        Log ("GIT_BACKEND=WINDOWS " + $winGit.Source)
    } else {
        Log 'GIT_BACKEND=WSL (Git for Windows not installed; this is supported)'
    }

    # Probe the WSL build environment before cloning/building anything expensive.
    # WSL git is sufficient; Git for Windows is deliberately NOT required.
    $probe = (& wsl.exe bash -lc 'missing=""; for x in git make python3 arm-none-eabi-gcc arm-none-eabi-readelf; do command -v "$x" >/dev/null 2>&1 || missing="$missing $x"; done; printf "MISSING=%s\n" "$missing"' 2>&1) -join "`n"
    Add-Content -Path $Log -Value $probe -Encoding UTF8
    Write-Host $probe
    if ($probe -match 'MISSING=\s*(.+)' -and $Matches[1].Trim()) {
        throw ("WSL toolchain incomplete. Missing:" + $Matches[1] + ". Install the SoulGold/pokeemerald-expansion WSL prerequisites, then rerun this same file.")
    }

    Log 'STEP=BOOTSTRAP_AND_BUILD'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Here 'S0_BOOTSTRAP.ps1') -Workspace $Workspace -BuildSoulGold -NoPause
    if ($LASTEXITCODE -ne 0) { throw "S0_BOOTSTRAP failed: $LASTEXITCODE" }

    $sg = Join-Path $Workspace 'soulgold'
    $gb = Join-Path $Workspace 'gbarecomp'
    $sgWsl = WslPath $sg
    $gbWsl = WslPath $gb

    Log 'STEP=IMPORT_SYMBOLS'
    $importerWin = Join-Path $Here 'S0_IMPORT_SYMBOLS.py'
    $importerWsl = WslPath $importerWin
    $cmd = "python3 '$importerWsl' --soulgold '$sgWsl' --gbarecomp '$gbWsl'"
    & wsl.exe bash -lc $cmd 2>&1 | ForEach-Object {
        Add-Content -Path $Log -Value $_ -Encoding UTF8
        Write-Host $_
    }
    if ($LASTEXITCODE -ne 0) { throw "S0_IMPORT_SYMBOLS failed: $LASTEXITCODE" }

    Log 'STEP=PREPARE_RUNNER'
    $prepareWin = Join-Path $Here 'S0_PREPARE_RUNNER.py'
    $prepareWsl = WslPath $prepareWin
    $wsWsl = WslPath $Workspace
    $cmd = "python3 '$prepareWsl' --workspace '$wsWsl'"
    & wsl.exe bash -lc $cmd 2>&1 | ForEach-Object {
        Add-Content -Path $Log -Value $_ -Encoding UTF8
        Write-Host $_
    }
    if ($LASTEXITCODE -ne 0) { throw "S0_PREPARE_RUNNER failed: $LASTEXITCODE" }

    $authority = Join-Path $Workspace 'SoulGoldRecomp\S0_RUNNER_AUTHORITY.txt'
    if (-not (Test-Path $authority)) { throw 'Runner authority file was not produced.' }
    foreach ($line in Get-Content $authority) { Log "AUTH $line" }

    Log 'RESULT=PASS'
    Write-Host ''
    Write-Host 'S0-A PASS: SoulGold built, hashed, symbols imported, minimal runner prepared.' -ForegroundColor Green
    Write-Host "Return the _evidence folder (or ZIP it) plus: $authority"
}
catch {
    Log 'RESULT=FAIL'
    Log ("ERROR=" + $_.Exception.Message)
    Write-Host ''
    Write-Host 'S0-A stopped safely. Nothing was promoted.' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host "Return this log: $Log"
    Read-Host 'Press Enter to close'
    exit 1
}

Read-Host 'Press Enter to close'
