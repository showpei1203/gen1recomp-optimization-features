param(
    [string]$EvidenceRoot = "$env:USERPROFILE\SoulGoldRecomp_S0\_evidence"
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Log = Join-Path $EvidenceRoot ("S0_STAGE_B_{0}.log" -f $Stamp)

$SoulGoldCommit = 'a6efa38348f978348da9dc4f4a7878cccf27bfd0'
$GbaRecompCommit = 'ed9824b70aa350cd9e1653894beaf6b1b6b27787'

function Log([string]$s) {
    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $s
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Host $line
}

function Invoke-WslCapture([string]$Label, [string[]]$CommandArgs) {
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $lines = @(& wsl.exe @CommandArgs 2>&1)
        $rc = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $saved }
    foreach ($line in $lines) { Log "$Label $line" }
    if ($rc -ne 0) { throw "$Label failed ($rc): $($CommandArgs -join ' ')" }
    return ,$lines
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

function Wsl-ToolExists([string]$name) {
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & wsl.exe which $name *> $null
        $rc = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $saved }
    return ($rc -eq 0)
}

function Install-BuildPrereqsIfNeeded {
    $required = @('cmake','ninja','pkg-config','g++')
    $missing = @()
    foreach ($tool in $required) {
        if (-not (Wsl-ToolExists $tool)) { $missing += $tool }
    }

    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & wsl.exe pkg-config --exists sdl2 *> $null
        $sdlRc = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $saved }
    if ($sdlRc -ne 0) { $missing += 'libsdl2-dev' }

    if ($missing.Count -eq 0) {
        Log 'S0B_PREREQS_OK=1'
        return
    }

    Log ("S0B_PREREQS_MISSING=" + ($missing -join ','))
    Write-Host ''
    Write-Host 'S0-B needs a few host-build packages inside WSL.' -ForegroundColor Yellow
    Write-Host 'If sudo asks for your WSL password, type it and press Enter.' -ForegroundColor Yellow
    Write-Host 'Linux will not show characters while the password is typed.' -ForegroundColor Yellow
    Write-Host ''

    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & wsl.exe sudo apt-get update
        $rc = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $saved }
    if ($rc -ne 0) { throw "apt-get update failed: $rc" }

    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & wsl.exe sudo apt-get install -y cmake ninja-build pkg-config libsdl2-dev
        $rc = $LASTEXITCODE
    }
    finally { $ErrorActionPreference = $saved }
    if ($rc -ne 0) { throw "S0-B prerequisite install failed: $rc" }

    foreach ($tool in $required) {
        if (-not (Wsl-ToolExists $tool)) { throw "WSL tool still missing after install: $tool" }
    }
    Log 'S0B_PREREQS_INSTALLED=1'
}

try {
    Log 'S0_STAGE_B_BEGIN'
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
        throw 'WSL is not available.'
    }

    Install-BuildPrereqsIfNeeded

    $homeLines = Invoke-WslCapture 'WSL_HOME' @('python3','-c','from pathlib import Path; print(Path.home())')
    $WslHome = (($homeLines | Select-Object -Last 1).ToString()).Trim()
    if (-not $WslHome.StartsWith('/')) { throw "Unexpected WSL HOME: $WslHome" }

    $ws = "$WslHome/SoulGoldRecomp_S0"
    $sg = "$ws/soulgold"
    $gb = "$ws/gbarecomp"
    $runner = "$ws/SoulGoldRecomp"
    $engineBuild = "$gb/build-s0"
    $runnerBuild = "$runner/build-s0"
    $rom = "$sg/Soulgold_Beta_1.gba"
    $gameToml = "$runner/variants/soulgold/game.toml"
    $symbolsDir = "$runner/variants/soulgold/symbols"
    $symbolOverlay = "$symbolsDir/SOULGOLD_BETA1_symbols.toml"
    $runtimeCopies = "$symbolsDir/SOULGOLD_runtime_copies.toml"
    $symbols = "$symbolsDir/imported_symbols.tsv"
    $dataSymbols = "$symbolsDir/imported_data_symbols.tsv"
    $generated = "$runner/variants/soulgold/generated"

    Log "WSL_WORKSPACE=$ws"

    foreach ($p in @($rom,$gameToml,$symbolOverlay,$runtimeCopies,$symbols,$dataSymbols,"$gb/CMakeLists.txt","$runner/CMakeLists.txt")) {
        if (-not (Wsl-Exists $p)) { throw "S0-A prerequisite missing: $p" }
    }

    $sgHead = ((Invoke-WslCapture 'SOULGOLD_HEAD' @('git','-C',$sg,'rev-parse','HEAD') | Select-Object -Last 1).ToString()).Trim()
    $gbHead = ((Invoke-WslCapture 'GBARECOMP_HEAD' @('git','-C',$gb,'rev-parse','HEAD') | Select-Object -Last 1).ToString()).Trim()
    if ($sgHead -ne $SoulGoldCommit) { throw "SoulGold pin drift: $sgHead" }
    if ($gbHead -ne $GbaRecompCommit) { throw "GBARecomp pin drift: $gbHead" }
    Log 'S0B_PINS_OK=1'

    $jobs = ((Invoke-WslCapture 'NPROC' @('nproc') | Select-Object -Last 1).ToString()).Trim()
    if ($jobs -notmatch '^\d+$') { $jobs = '4' }

    Log 'STEP=CONFIGURE_GBARECOMP'
    Invoke-WslStream 'CMAKE[ENGINE]' @(
        'cmake','-S',$gb,'-B',$engineBuild,'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release','-DGBARECOMP_ENABLE_MODS=ON'
    )

    Log 'STEP=BUILD_GBA_RECOMPILE'
    Invoke-WslStream 'BUILD[RECOMPILER]' @('cmake','--build',$engineBuild,'--target','gba_recompile','-j',$jobs)

    $recompiler = "$engineBuild/gba_recompile"
    if (-not (Wsl-Exists $recompiler)) { throw "gba_recompile not produced: $recompiler" }
    $recompilerSha = (((Invoke-WslCapture 'RECOMPILER_SHA256' @('sha256sum',$recompiler) | Select-Object -Last 1).ToString()).Split(' ')[0]).Trim()
    Log "GBA_RECOMPILE_SHA256=$recompilerSha"

    Log 'STEP=CLEAN_GENERATED_OUTPUT'
    Invoke-WslStream 'CLEAN[GENERATED]' @('rm','-rf',$generated)
    Invoke-WslStream 'MKDIR[GENERATED]' @('mkdir','-p',$generated)

    Log 'STEP=RECOMPILE_SOULGOLD'
    Invoke-WslStream 'RECOMPILE' @(
        $recompiler,
        '--rom',$rom,
        '--entry','0x08000000',
        '--symbols',$symbols,
        '--data-symbols',$dataSymbols,
        '--config',$gameToml,
        '--config',$symbolOverlay,
        '--config',$runtimeCopies,
        '--out',$generated,
        '--max-functions','65536',
        '--codegen-shards','64'
    )

    foreach ($p in @("$generated/recompiled.h","$generated/dispatch_table.cpp","$generated/symbol_map.cpp","$generated/data_symbol_map.cpp")) {
        if (-not (Wsl-Exists $p)) { throw "generated output missing: $p" }
    }

    $shardLines = Invoke-WslCapture 'SHARDS' @('find',$generated,'-maxdepth','1','-type','f','-name','recompiled_*.cpp')
    $shardCount = @($shardLines | Where-Object { $_ -and $_.ToString().StartsWith('/') }).Count
    Log "GENERATED_SHARD_COUNT=$shardCount"
    if ($shardCount -lt 2) { throw "Too few generated shards: $shardCount" }

    Log 'STEP=CONFIGURE_SOULGOLD_RUNNER'
    Invoke-WslStream 'CMAKE[RUNNER]' @(
        'cmake','-S',$runner,'-B',$runnerBuild,'-G','Ninja',
        '-DCMAKE_BUILD_TYPE=Release',
        "-DGBARECOMP_ROOT=$gb",
        '-DGBARECOMP_ENABLE_MODS=ON'
    )

    Log 'STEP=LINK_SOULGOLD_RUNNER'
    Invoke-WslStream 'BUILD[RUNNER]' @('cmake','--build',$runnerBuild,'--target','SoulGoldRecomp','-j',$jobs)

    $runnerExe = "$runnerBuild/SoulGoldRecomp"
    if (-not (Wsl-Exists $runnerExe)) { throw "SoulGoldRecomp runner not produced: $runnerExe" }
    $runnerSize = ((Invoke-WslCapture 'RUNNER_SIZE' @('stat','-c','%s',$runnerExe) | Select-Object -Last 1).ToString()).Trim()
    $runnerSha = (((Invoke-WslCapture 'RUNNER_SHA256' @('sha256sum',$runnerExe) | Select-Object -Last 1).ToString()).Split(' ')[0]).Trim()
    $sdlVersion = ((Invoke-WslCapture 'SDL_VERSION' @('pkg-config','--modversion','sdl2') | Select-Object -Last 1).ToString()).Trim()

    Log "RUNNER_PATH=$runnerExe"
    Log "RUNNER_SIZE=$runnerSize"
    Log "RUNNER_SHA256=$runnerSha"
    Log "SDL2_VERSION=$sdlVersion"

    $authorityPath = Join-Path $EvidenceRoot 'S0_B_AUTHORITY.txt'
    @(
        'SOULGOLDRECOMP S0-B AUTHORITY',
        'RESULT=PASS',
        "SOULGOLD_COMMIT=$SoulGoldCommit",
        "GBARECOMP_COMMIT=$GbaRecompCommit",
        "GBA_RECOMPILE_SHA256=$recompilerSha",
        "GENERATED_SHARD_COUNT=$shardCount",
        "RUNNER_PATH=$runnerExe",
        "RUNNER_SIZE=$runnerSize",
        "RUNNER_SHA256=$runnerSha",
        "SDL2_VERSION=$sdlVersion",
        'S0B_GATE=NATIVE_SHARDS_GENERATED_AND_RUNNER_LINKED',
        'NEXT=S0-C_RUNTIME_BOOT_TITLE_SCREEN'
    ) | Set-Content -Encoding UTF8 $authorityPath

    Log 'RESULT=PASS'
    $zip = Join-Path $EvidenceRoot ("SOULGOLD_S0_B_EVIDENCE_{0}.zip" -f $Stamp)
    Compress-Archive -Path @($Log,$authorityPath) -DestinationPath $zip -Force

    Write-Host ''
    Write-Host 'S0-B PASS: native SoulGold shards generated and SoulGoldRecomp runner linked.' -ForegroundColor Green
    Write-Host "Evidence ZIP: $zip"
    Write-Host 'Next gate: S0-C runtime boot / title-screen validation.'
}
catch {
    Log 'RESULT=FAIL'
    Log ("ERROR=" + $_.Exception.Message)
    Write-Host ''
    Write-Host 'S0-B stopped safely. S0-A remains sealed.' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host "Return this log: $Log"
    Read-Host 'Press Enter to close'
    exit 1
}

Read-Host 'Press Enter to close'
