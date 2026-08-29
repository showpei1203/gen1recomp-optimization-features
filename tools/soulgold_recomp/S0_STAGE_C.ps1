param(
    [string]$EvidenceRoot = "$env:USERPROFILE\SoulGoldRecomp_S0\_evidence"
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Log = Join-Path $EvidenceRoot ("S0_STAGE_C_{0}.log" -f $Stamp)

$ExpectedRunnerSha256 = '08647605065305fda3bdd9c13954a5626c500b95b48c790c8f7d00ccb3cf7200'
$ExpectedRomSha1 = 'd88b6a59802ccd442275ecbcfc9140fff34556dc'
$ExpectedBiosSha1 = '300c20df6731a33952ded8c436f7f186d25d3492'
$ExpectedBiosSize = 16384

function Log([string]$s) {
    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $s
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Host $line
}

function Invoke-WslScalar([string[]]$CommandArgs) {
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $lines = @(& wsl.exe @CommandArgs 2>&1)
        $rc = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $saved }
    if ($rc -ne 0) {
        throw "WSL command failed ($rc): $($CommandArgs -join ' ') :: $($lines -join ' | ')"
    }
    if ($lines.Count -eq 0) { return '' }
    return (($lines | Select-Object -Last 1).ToString()).Trim()
}

function Invoke-WslStream([string]$Label, [string[]]$CommandArgs) {
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & wsl.exe @CommandArgs 2>&1 | ForEach-Object { Log "$Label $_" }
        $rc = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $saved }
    if ($rc -ne 0) { throw "$Label failed ($rc): $($CommandArgs -join ' ')" }
}

function Wsl-Exists([string]$path) {
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & wsl.exe test -e $path 2>$null
        $rc = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $saved }
    return ($rc -eq 0)
}

function WinPath-ToWslMount([string]$p) {
    $full = (Resolve-Path $p).Path
    if ($full -notmatch '^([A-Za-z]):\\(.*)$') {
        throw "Unsupported Windows path for WSL mount conversion: $full"
    }
    $drive = $Matches[1].ToLowerInvariant()
    $rest = $Matches[2].Replace([char]92, [char]47)
    return "/mnt/$drive/$rest"
}

function Test-WindowsBios([string]$Path) {
    if (-not (Test-Path $Path -PathType Leaf)) { return $false }
    $fi = Get-Item $Path
    if ($fi.Length -ne $ExpectedBiosSize) { return $false }
    $sha = (Get-FileHash $Path -Algorithm SHA1).Hash.ToLowerInvariant()
    return ($sha -eq $ExpectedBiosSha1)
}

function Select-OwnBios {
    $candidates = @(
        (Join-Path $Here 'gba_bios.bin'),
        (Join-Path $env:USERPROFILE 'Downloads\gba_bios.bin'),
        (Join-Path $env:USERPROFILE 'Desktop\gba_bios.bin'),
        (Join-Path $env:USERPROFILE 'Documents\gba_bios.bin')
    )
    foreach ($candidate in $candidates) {
        if (Test-WindowsBios $candidate) {
            Log "BIOS_SOURCE_AUTO=$candidate"
            return (Resolve-Path $candidate).Path
        }
    }

    Add-Type -AssemblyName System.Windows.Forms
    $dlg = New-Object System.Windows.Forms.OpenFileDialog
    $dlg.Title = 'Select your own GBA BIOS dump (gba_bios.bin)'
    $dlg.Filter = 'GBA BIOS (*.bin)|*.bin|All files (*.*)|*.*'
    $dlg.Multiselect = $false
    if ($dlg.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        throw 'No GBA BIOS selected. S0-C requires your own legally obtained 16KB GBA BIOS dump.'
    }
    if (-not (Test-WindowsBios $dlg.FileName)) {
        $len = (Get-Item $dlg.FileName).Length
        $sha = (Get-FileHash $dlg.FileName -Algorithm SHA1).Hash.ToLowerInvariant()
        throw "Selected BIOS is not the expected GBA BIOS: size=$len sha1=$sha"
    }
    Log "BIOS_SOURCE_SELECTED=$($dlg.FileName)"
    return $dlg.FileName
}

try {
    Log 'S0_STAGE_C_BEGIN'
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
        throw 'WSL is not available.'
    }

    $WslHome = Invoke-WslScalar @('python3','-c','from pathlib import Path; print(Path.home())')
    if (-not $WslHome.StartsWith('/')) { throw "Unexpected WSL HOME: $WslHome" }

    $ws = "$WslHome/SoulGoldRecomp_S0"
    $sg = "$ws/soulgold"
    $gb = "$ws/gbarecomp"
    $runnerRoot = "$ws/SoulGoldRecomp"
    $runner = "$runnerRoot/build-s0/SoulGoldRecomp"
    $rom = "$sg/Soulgold_Beta_1.gba"
    $gameToml = "$runnerRoot/variants/soulgold/game.toml"
    $bios = "$gb/bios/gba_bios.bin"
    $runDir = "$ws/_s0c"
    $pngWsl = "$runDir/S0C_frame_$Stamp.png"
    $coverageWsl = "$runDir/S0C_coverage_$Stamp.json"
    $missWsl = "$runDir/S0C_misses_$Stamp.toml.frag"

    Log "WSL_WORKSPACE=$ws"

    foreach ($p in @($runner,$rom,$gameToml)) {
        if (-not (Wsl-Exists $p)) { throw "S0-C prerequisite missing: $p" }
    }

    $runnerSha = (Invoke-WslScalar @('sha256sum',$runner)).Split(' ')[0].Trim()
    Log "RUNNER_SHA256=$runnerSha"
    if ($runnerSha -ne $ExpectedRunnerSha256) {
        throw "S0-B runner drift: got $runnerSha expected $ExpectedRunnerSha256"
    }

    $romSha = (Invoke-WslScalar @('sha1sum',$rom)).Split(' ')[0].Trim()
    Log "ROM_SHA1=$romSha"
    if ($romSha -ne $ExpectedRomSha1) {
        throw "SoulGold ROM drift: got $romSha expected $ExpectedRomSha1"
    }

    if (-not (Wsl-Exists $bios)) {
        Log 'BIOS_WSL_PRESENT=0'
        $selected = Select-OwnBios
        $selectedWsl = WinPath-ToWslMount $selected
        Invoke-WslStream 'BIOS[MKDIR]' @('mkdir','-p',"$gb/bios")
        Invoke-WslStream 'BIOS[COPY]' @('cp',$selectedWsl,$bios)
    } else {
        Log 'BIOS_WSL_PRESENT=1'
    }

    $biosSize = Invoke-WslScalar @('stat','-c','%s',$bios)
    $biosSha = (Invoke-WslScalar @('sha1sum',$bios)).Split(' ')[0].Trim()
    Log "BIOS_SIZE=$biosSize"
    Log "BIOS_SHA1=$biosSha"
    if ([int64]$biosSize -ne $ExpectedBiosSize -or $biosSha -ne $ExpectedBiosSha1) {
        throw "WSL BIOS identity mismatch: size=$biosSize sha1=$biosSha"
    }

    Invoke-WslStream 'S0C[MKDIR]' @('mkdir','-p',$runDir)
    foreach ($p in @($pngWsl,$coverageWsl,$missWsl)) {
        $saved = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            & wsl.exe rm -f $p *> $null
        }
        finally { $ErrorActionPreference = $saved }
    }

    Log 'STEP=HEADLESS_BOOT_1200_FRAMES'
    Log 'BOOT_POLICY=BIOS_HLE_SKIP_INTRO'

    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & wsl.exe env `
            "GBARECOMP_COVERAGE_JSON=$coverageWsl" `
            "GBARECOMP_MISS_FRAG=$missWsl" `
            $runner `
            --config $gameToml `
            --bios $bios `
            --rom $rom `
            --bios-hle `
            --no-window `
            --frames 1200 `
            --dump-png $pngWsl 2>&1 | ForEach-Object { Log "RUN $_" }
        $runRc = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $saved }

    Log "RUN_EXIT_CODE=$runRc"
    if ($runRc -ne 0) {
        throw "SoulGoldRecomp headless boot failed with exit code $runRc"
    }
    if (-not (Wsl-Exists $pngWsl)) { throw 'Runtime returned 0 but no PNG framebuffer was produced.' }

    $pngSize = Invoke-WslScalar @('stat','-c','%s',$pngWsl)
    if ([int64]$pngSize -lt 128) { throw "Framebuffer PNG is implausibly small: $pngSize bytes" }
    Log "FRAMEBUFFER_PNG_SIZE=$pngSize"

    $evidenceWsl = WinPath-ToWslMount $EvidenceRoot
    $pngLocal = Join-Path $EvidenceRoot ("S0C_frame_$Stamp.png")
    $coverageLocal = Join-Path $EvidenceRoot ("S0C_coverage_$Stamp.json")
    $missLocal = Join-Path $EvidenceRoot ("S0C_misses_$Stamp.toml.frag")

    Invoke-WslStream 'COPY[PNG]' @('cp',$pngWsl,"$evidenceWsl/S0C_frame_$Stamp.png")
    if (Wsl-Exists $coverageWsl) {
        Invoke-WslStream 'COPY[COVERAGE]' @('cp',$coverageWsl,"$evidenceWsl/S0C_coverage_$Stamp.json")
        Log 'COVERAGE_PRESENT=1'
    } else {
        Log 'COVERAGE_PRESENT=0'
    }
    if (Wsl-Exists $missWsl) {
        Invoke-WslStream 'COPY[MISSES]' @('cp',$missWsl,"$evidenceWsl/S0C_misses_$Stamp.toml.frag")
        Log 'MISS_REPORT_PRESENT=1'
    } else {
        Log 'MISS_REPORT_PRESENT=0'
    }

    $authorityPath = Join-Path $EvidenceRoot 'S0_C_CANDIDATE_AUTHORITY.txt'
    @(
        'SOULGOLDRECOMP S0-C CANDIDATE AUTHORITY',
        'RESULT=CANDIDATE_PASS',
        "RUNNER_SHA256=$runnerSha",
        "ROM_SHA1=$romSha",
        "BIOS_SHA1=$biosSha",
        'BOOT_POLICY=BIOS_HLE_SKIP_INTRO',
        'FRAMES_REQUESTED=1200',
        "RUN_EXIT_CODE=$runRc",
        "FRAMEBUFFER_PNG=$pngLocal",
        "FRAMEBUFFER_PNG_SIZE=$pngSize",
        "COVERAGE_FILE=$coverageLocal",
        "MISS_FILE=$missLocal",
        'FORMAL_PASS=REQUIRES_ASSISTANT_FRAMEBUFFER_AND_COVERAGE_REVIEW',
        'NEXT_IF_HEALTHY=S0-C_INTERACTIVE_TITLE_SCREEN'
    ) | Set-Content -Encoding UTF8 $authorityPath

    Log 'RESULT=CANDIDATE_PASS'

    $zip = Join-Path $EvidenceRoot ("SOULGOLD_S0_C_EVIDENCE_{0}.zip" -f $Stamp)
    $files = @($Log,$authorityPath,$pngLocal)
    if (Test-Path $coverageLocal) { $files += $coverageLocal }
    if (Test-Path $missLocal) { $files += $missLocal }
    Compress-Archive -Path $files -DestinationPath $zip -Force

    Write-Host ''
    Write-Host 'S0-C CANDIDATE PASS: 1200-frame headless run completed and framebuffer evidence was captured.' -ForegroundColor Green
    Write-Host 'Do not call S0-C formal PASS yet; return the evidence ZIP for framebuffer/coverage review.' -ForegroundColor Yellow
    Write-Host "Evidence ZIP: $zip"
}
catch {
    Log 'RESULT=FAIL'
    Log ("ERROR=" + $_.Exception.Message)
    Write-Host ''
    Write-Host 'S0-C stopped safely. S0-A and S0-B remain sealed.' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host "Return this log: $Log"
    Read-Host 'Press Enter to close'
    exit 1
}

Read-Host 'Press Enter to close'
