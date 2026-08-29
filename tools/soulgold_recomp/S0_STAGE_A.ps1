param(
    [string]$EvidenceRoot = "$env:USERPROFILE\SoulGoldRecomp_S0\_evidence"
)

$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Log = Join-Path $EvidenceRoot ("S0_STAGE_A_WSLNATIVE_{0}.log" -f $Stamp)

$SoulGoldRepo = 'https://github.com/Eemeliri/soulgold.git'
$SoulGoldCommit = 'a6efa38348f978348da9dc4f4a7878cccf27bfd0'
$GbaRecompRepo = 'https://github.com/mstan/gbarecomp.git'
$GbaRecompCommit = 'ed9824b70aa350cd9e1653894beaf6b1b6b27787'
$EmeraldRecompCommit = '4e1f89669b9945e338c0f2e52816aa0533fa30d3'

function Log([string]$s) {
    $line = '[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $s
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Host $line
}

function WinPath-ToWslMount([string]$p) {
    $full = (Resolve-Path $p).Path
    if ($full -notmatch '^([A-Za-z]):\\(.*)$') {
        throw "Unsupported Windows path for WSL mount conversion: $full"
    }
    $drive = $Matches[1].ToLowerInvariant()
    $rest = $Matches[2].Replace('\\', '/')
    return "/mnt/$drive/$rest"
}

function Invoke-Wsl([string]$Label, [string[]]$Args) {
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $lines = @(& wsl.exe @Args 2>&1)
        $rc = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $saved
    }
    foreach ($line in $lines) { Log "$Label $line" }
    if ($rc -ne 0) { throw "$Label failed ($rc): $($Args -join ' ')" }
    return ,$lines
}

function Wsl-Exists([string]$path) {
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        & wsl.exe test -e $path 2>$null
        $rc = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $saved
    }
    return ($rc -eq 0)
}

function Clone-Pinned([string]$Name, [string]$Url, [string]$Commit, [string]$Dest) {
    if (-not (Wsl-Exists "$Dest/.git")) {
        Log "CLONE $Name $Url -> $Dest"
        Invoke-Wsl "GIT[$Name]" @('git','clone','--recurse-submodules',$Url,$Dest) | Out-Null
    } else {
        Log "EXISTS $Name $Dest"
        Invoke-Wsl "GIT[$Name]" @('git','-C',$Dest,'fetch','origin',$Commit) | Out-Null
    }
    Invoke-Wsl "GIT[$Name]" @('git','-C',$Dest,'checkout','--detach',$Commit) | Out-Null
    Invoke-Wsl "GIT[$Name]" @('git','-C',$Dest,'submodule','update','--init','--recursive') | Out-Null
    $headLines = Invoke-Wsl "HEAD[$Name]" @('git','-C',$Dest,'rev-parse','HEAD')
    $head = (($headLines | Select-Object -Last 1).ToString()).Trim()
    if ($head -ne $Commit) { throw "$Name pin mismatch: expected $Commit got $head" }
    Log "PIN_OK $Name $head"
}

try {
    Log 'S0_STAGE_A_WSLNATIVE_BEGIN'
    if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
        throw 'WSL is not available.'
    }

    $required = @('git','make','python3','arm-none-eabi-gcc','arm-none-eabi-readelf','sha1sum','sha256sum','stat')
    foreach ($tool in $required) {
        $saved = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            & wsl.exe which $tool *> $null
            $rc = $LASTEXITCODE
        }
        finally { $ErrorActionPreference = $saved }
        if ($rc -ne 0) { throw "WSL tool missing: $tool" }
        Log "WSL_TOOL_OK=$tool"
    }

    $homeLines = Invoke-Wsl 'WSL_HOME' @('printenv','HOME')
    $WslHome = (($homeLines | Select-Object -Last 1).ToString()).Trim()
    if (-not $WslHome.StartsWith('/')) { throw "Unexpected WSL HOME: $WslHome" }
    $WslWorkspace = "$WslHome/SoulGoldRecomp_S0"
    $sg = "$WslWorkspace/soulgold"
    $gb = "$WslWorkspace/gbarecomp"
    Log "WSL_WORKSPACE=$WslWorkspace"
    Invoke-Wsl 'MKDIR' @('mkdir','-p',$WslWorkspace) | Out-Null

    Clone-Pinned 'soulgold' $SoulGoldRepo $SoulGoldCommit $sg
    Clone-Pinned 'gbarecomp' $GbaRecompRepo $GbaRecompCommit $gb
    Log 'UPSTREAM_PINS_OK=1'

    $nprocLines = Invoke-Wsl 'NPROC' @('nproc')
    $jobs = (($nprocLines | Select-Object -Last 1).ToString()).Trim()
    if ($jobs -notmatch '^\d+$') { $jobs = '4' }
    Log "SOULGOLD_BUILD_START jobs=$jobs"
    Invoke-Wsl 'MAKE' @('make','-C',$sg,"-j$jobs") | Out-Null
    Log 'SOULGOLD_BUILD_EXIT=0'

    $rom = "$sg/Soulgold_Beta_1.gba"
    $elf = "$sg/Soulgold_Beta_1.elf"
    $map = "$sg/Soulgold_Beta_1.map"
    $sym = "$sg/Soulgold_Beta_1.sym"
    foreach ($p in @($rom,$elf,$map,$sym)) {
        if (-not (Wsl-Exists $p)) { throw "Required SoulGold artifact missing: $p" }
    }

    $sizeLines = Invoke-Wsl 'ROM_SIZE' @('stat','-c','%s',$rom)
    $sha1Lines = Invoke-Wsl 'ROM_SHA1' @('sha1sum',$rom)
    $sha256Lines = Invoke-Wsl 'ROM_SHA256' @('sha256sum',$rom)
    $romSize = (($sizeLines | Select-Object -Last 1).ToString()).Trim()
    $romSha1 = ((($sha1Lines | Select-Object -Last 1).ToString()).Split(' ')[0]).Trim()
    $romSha256 = ((($sha256Lines | Select-Object -Last 1).ToString()).Split(' ')[0]).Trim()
    Log "ROM_AUTHORITY size=$romSize sha1=$romSha1 sha256=$romSha256"

    $importerWsl = WinPath-ToWslMount (Join-Path $Here 'S0_IMPORT_SYMBOLS.py')
    $prepareWsl = WinPath-ToWslMount (Join-Path $Here 'S0_PREPARE_RUNNER.py')

    Log 'STEP=IMPORT_SYMBOLS'
    Invoke-Wsl 'IMPORT' @('python3',$importerWsl,'--soulgold',$sg,'--gbarecomp',$gb) | Out-Null

    Log 'STEP=PREPARE_RUNNER'
    Invoke-Wsl 'PREPARE' @('python3',$prepareWsl,'--workspace',$WslWorkspace) | Out-Null

    $runnerAuthorityWsl = "$WslWorkspace/SoulGoldRecomp/S0_RUNNER_AUTHORITY.txt"
    $symbolReportWsl = "$sg/_recomp_symbols/S0_SYMBOL_IMPORT_REPORT.txt"
    if (-not (Wsl-Exists $runnerAuthorityWsl)) { throw 'Runner authority was not produced.' }
    if (-not (Wsl-Exists $symbolReportWsl)) { throw 'Symbol import report was not produced.' }

    $runnerLines = Invoke-Wsl 'RUNNER_AUTH' @('cat',$runnerAuthorityWsl)
    $symbolLines = Invoke-Wsl 'SYMBOL_AUTH' @('cat',$symbolReportWsl)
    $runnerLocal = Join-Path $EvidenceRoot 'S0_RUNNER_AUTHORITY.txt'
    $symbolLocal = Join-Path $EvidenceRoot 'S0_SYMBOL_IMPORT_REPORT.txt'
    $runnerLines | Set-Content -Encoding UTF8 $runnerLocal
    $symbolLines | Set-Content -Encoding UTF8 $symbolLocal

    $sourceAuthority = [ordered]@{
        captured_at = (Get-Date).ToString('o')
        wsl_workspace = $WslWorkspace
        pins = [ordered]@{
            soulgold = $SoulGoldCommit
            gbarecomp = $GbaRecompCommit
            emeraldrecomp_reference = $EmeraldRecompCommit
        }
        rom = [ordered]@{
            path = $rom
            size = [int64]$romSize
            sha1 = $romSha1
            sha256 = $romSha256
        }
    }
    $sourceAuthority | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $EvidenceRoot 'S0_SOURCE_AUTHORITY.json')

    Log 'RESULT=PASS'
    $zip = Join-Path $EvidenceRoot ("SOULGOLD_S0_A_EVIDENCE_{0}.zip" -f $Stamp)
    $files = @(
        $Log,
        $runnerLocal,
        $symbolLocal,
        (Join-Path $EvidenceRoot 'S0_SOURCE_AUTHORITY.json')
    )
    Compress-Archive -Path $files -DestinationPath $zip -Force
    Write-Host ''
    Write-Host 'S0-A PASS: WSL-native SoulGold build, symbol import and runner preparation completed.' -ForegroundColor Green
    Write-Host "Evidence ZIP: $zip"
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
