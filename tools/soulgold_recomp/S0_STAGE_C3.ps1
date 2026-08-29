param(
    [string]$EvidenceRoot = "$env:USERPROFILE\SoulGoldRecomp_S0\_evidence"
)

$ErrorActionPreference='Stop'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null
$Log=Join-Path $EvidenceRoot ("S0_STAGE_C3_{0}.log" -f $Stamp)

$ExpectedRunnerSha='08647605065305fda3bdd9c13954a5626c500b95b48c790c8f7d00ccb3cf7200'
$ExpectedRomSha='d88b6a59802ccd442275ecbcfc9140fff34556dc'
$ExpectedBiosSha='300c20df6731a33952ded8c436f7f186d25d3492'

function Log([string]$s) {
    $line='[{0}] {1}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'),$s
    Add-Content -Path $Log -Value $line -Encoding UTF8
    Write-Host $line
}
function Scalar([string[]]$CommandArgs) {
    $old=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        $x=@(& wsl.exe @CommandArgs 2>&1)
        $rc=$LASTEXITCODE
    } finally { $ErrorActionPreference=$old }
    if($rc -ne 0){ throw "WSL failed ($rc): $($CommandArgs -join ' ') :: $($x -join ' | ')" }
    if($x.Count -eq 0){return ''}
    return (($x|Select-Object -Last 1).ToString()).Trim()
}
function Get-WslEnvValue([string]$Name) {
    $old=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        $x=@(& wsl.exe printenv $Name 2>&1)
        $rc=$LASTEXITCODE
    } finally { $ErrorActionPreference=$old }
    if($rc -eq 0) {
        if($x.Count -eq 0){ return '' }
        return (($x|Select-Object -Last 1).ToString()).Trim()
    }
    if($rc -eq 1) { return '' }
    throw "WSL printenv failed ($rc) for $Name :: $($x -join ' | ')"
}
function Stream([string]$label,[string[]]$CommandArgs) {
    $old=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        & wsl.exe @CommandArgs 2>&1 | ForEach-Object { Log "$label $_" }
        $rc=$LASTEXITCODE
    } finally { $ErrorActionPreference=$old }
    if($rc -ne 0){throw "$label failed ($rc)"}
}
function Exists([string]$p) {
    $old=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        & wsl.exe test -e $p 2>$null
        $rc=$LASTEXITCODE
    } finally {$ErrorActionPreference=$old}
    return $rc -eq 0
}
function WinToWsl([string]$p) {
    $full=(Resolve-Path $p).Path
    if($full -notmatch '^([A-Za-z]):\\(.*)$'){throw "Unsupported Windows path: $full"}
    $d=$Matches[1].ToLowerInvariant()
    $r=$Matches[2].Replace([char]92,[char]47)
    return "/mnt/$d/$r"
}

try {
    Log 'S0_STAGE_C3_BEGIN'
    $WslHomePath=Scalar @('python3','-c','from pathlib import Path; print(Path.home())')
    if(-not $WslHomePath.StartsWith('/')){throw "Unexpected WSL HOME: $WslHomePath"}

    $ws="$WslHomePath/SoulGoldRecomp_S0"
    $sg="$ws/soulgold"
    $gb="$ws/gbarecomp"
    $rr="$ws/SoulGoldRecomp"
    $runner="$rr/build-s0/SoulGoldRecomp"
    $rom="$sg/Soulgold_Beta_1.gba"
    $bios="$gb/bios/gba_bios.bin"
    $config="$rr/variants/soulgold/game.toml"
    $runDir="$ws/_s0c3"
    $save="$runDir/S0C3_manual_test.sav"
    $png="$runDir/S0C3_final_$Stamp.png"
    $cov="$runDir/S0C3_coverage_$Stamp.json"
    $miss="$runDir/S0C3_misses_$Stamp.toml.frag"
    $cadence="$runDir/S0C3_present_$Stamp.csv"

    Stream 'MKDIR' @('mkdir','-p',$runDir)
    foreach($p in @($runner,$rom,$bios,$config)){
        if(-not (Exists $p)){throw "Missing sealed prerequisite: $p"}
    }

    $rsha=(Scalar @('sha256sum',$runner)).Split(' ')[0].Trim()
    $romsha=(Scalar @('sha1sum',$rom)).Split(' ')[0].Trim()
    $biossha=(Scalar @('sha1sum',$bios)).Split(' ')[0].Trim()
    Log "RUNNER_SHA256=$rsha"
    Log "ROM_SHA1=$romsha"
    Log "BIOS_SHA1=$biossha"
    if($rsha -ne $ExpectedRunnerSha){throw "Runner drift: $rsha"}
    if($romsha -ne $ExpectedRomSha){throw "ROM drift: $romsha"}
    if($biossha -ne $ExpectedBiosSha){throw "BIOS drift: $biossha"}

    $WslDisplay=Get-WslEnvValue 'DISPLAY'
    $WslWaylandDisplay=Get-WslEnvValue 'WAYLAND_DISPLAY'
    Log "WSL_DISPLAY=$WslDisplay"
    Log "WSL_WAYLAND_DISPLAY=$WslWaylandDisplay"
    if([string]::IsNullOrWhiteSpace($WslDisplay) -and [string]::IsNullOrWhiteSpace($WslWaylandDisplay)){
        throw 'No WSL GUI display was detected. WSLg/X display is required for S0-C3 interactive validation.'
    }

    $checklist=Join-Path $EvidenceRoot 'S0_C3_MANUAL_CHECKLIST.txt'
    @(
        'SOULGOLDRECOMP S0-C3 MANUAL CHECKLIST','',
        'Keyboard:','  A=X','  B=Z','  Start=Enter','  Select=Right Shift',
        '  D-pad=Arrow keys','  L=C','  R=V','',
        'Required manual path:',
        '1. Confirm the emulator warning is visible.',
        '2. Press Enter once and confirm it progresses.',
        '3. Confirm the pret / pokeemerald-expansion splash.',
        '4. Confirm the Pokemon SoulGold title screen.',
        '5. Press Enter at the title screen.',
        '6. Verify arrows + X(A) + Z(B) respond in the next menu/intro.',
        '7. Start NEW GAME if offered and advance through several dialogue boxes.',
        '8. Confirm whether audio is audible and approximately synchronized.',
        '9. Leave the game on a meaningful post-title screen, then close the SDL window with the window X button.'
    ) | Set-Content -Path $checklist -Encoding UTF8

    Write-Host ''
    Write-Host '===============================================================' -ForegroundColor Cyan
    Write-Host 'S0-C3 MANUAL TEST' -ForegroundColor Cyan
    Write-Host '===============================================================' -ForegroundColor Cyan
    Write-Host 'A=X  B=Z  Start=Enter  Select=RightShift  D-pad=Arrows  L=C  R=V'
    Write-Host ''
    Write-Host 'Please progress from the emulator warning into the title screen,'
    Write-Host 'then press Start and test arrows / A / B. Start NEW GAME if offered.'
    Write-Host 'Advance several dialogue boxes, listen for audio, then close the'
    Write-Host 'game window using its X button. Evidence will be collected afterward.'
    Write-Host ''
    Read-Host 'Press Enter here to launch the interactive SoulGoldRecomp window'

    Log 'STEP=INTERACTIVE_WINDOW'
    $old=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'
        & wsl.exe env `
            "GBARECOMP_COVERAGE_JSON=$cov" `
            "GBARECOMP_MISS_FRAG=$miss" `
            "GBARECOMP_PRESENT_CADENCE=1" `
            "GBARECOMP_PRESENT_CADENCE_DUMP=$cadence" `
            $runner `
            --config $config `
            --bios $bios `
            --rom $rom `
            --bios-hle `
            --window `
            --scale 4 `
            --save-path $save `
            --dump-png $png 2>&1 |
            ForEach-Object { Log "RUN $_" }
        $runRc=$LASTEXITCODE
    } finally { $ErrorActionPreference=$old }
    Log "RUN_EXIT_CODE=$runRc"

    if($runRc -ne 0){throw "Interactive runner exited with code $runRc"}
    if(-not (Exists $png)){throw 'Interactive runner closed cleanly but final framebuffer PNG is missing.'}

    $evWsl=WinToWsl $EvidenceRoot
    $pngLocal=Join-Path $EvidenceRoot ("S0C3_final_$Stamp.png")
    $covLocal=Join-Path $EvidenceRoot ("S0C3_coverage_$Stamp.json")
    $missLocal=Join-Path $EvidenceRoot ("S0C3_misses_$Stamp.toml.frag")
    $cadLocal=Join-Path $EvidenceRoot ("S0C3_present_$Stamp.csv")
    $saveLocal=Join-Path $EvidenceRoot ("S0C3_manual_test_$Stamp.sav")

    Stream 'COPY[PNG]' @('cp',$png,"$evWsl/S0C3_final_$Stamp.png")
    if(Exists $cov){Stream 'COPY[COV]' @('cp',$cov,"$evWsl/S0C3_coverage_$Stamp.json")}
    if(Exists $miss){Stream 'COPY[MISS]' @('cp',$miss,"$evWsl/S0C3_misses_$Stamp.toml.frag")}
    if(Exists $cadence){Stream 'COPY[CADENCE]' @('cp',$cadence,"$evWsl/S0C3_present_$Stamp.csv")}
    if(Exists $save){Stream 'COPY[SAVE]' @('cp',$save,"$evWsl/S0C3_manual_test_$Stamp.sav")}

    $authority=Join-Path $EvidenceRoot 'S0_C3_CANDIDATE_AUTHORITY.txt'
    @(
        'SOULGOLDRECOMP S0-C3 CANDIDATE AUTHORITY','RESULT=CANDIDATE_PASS',
        "RUNNER_SHA256=$rsha","ROM_SHA1=$romsha","BIOS_SHA1=$biossha",
        'MODE=INTERACTIVE_WINDOW',"RUN_EXIT_CODE=$runRc","FINAL_FRAMEBUFFER=$pngLocal",
        "COVERAGE_FILE=$covLocal","MISS_FILE=$missLocal","PRESENT_CADENCE_FILE=$cadLocal",
        "TEST_SAVE=$saveLocal",'FORMAL_PASS=REQUIRES_USER_MANUAL_REPORT_AND_FRAMEBUFFER_REVIEW',
        'NEXT_IF_HEALTHY=S0-D_STATIC_COVERAGE_CLOSURE_AND_T0_TRANSLATION_AUDIT'
    ) | Set-Content -Path $authority -Encoding UTF8

    Log 'RESULT=CANDIDATE_PASS'
    $zip=Join-Path $EvidenceRoot ("SOULGOLD_S0_C3_EVIDENCE_{0}.zip" -f $Stamp)
    $files=@($Log,$authority,$checklist,$pngLocal)
    foreach($optional in @($covLocal,$missLocal,$cadLocal,$saveLocal)){
        if(Test-Path $optional){$files+=$optional}
    }
    Compress-Archive -Path $files -DestinationPath $zip -Force

    Write-Host ''
    Write-Host 'S0-C3 CANDIDATE PASS. Interactive session closed cleanly.' -ForegroundColor Green
    Write-Host 'Return the evidence ZIP and briefly report: controls / audio / where you reached.' -ForegroundColor Yellow
    Write-Host "Evidence ZIP: $zip"
}
catch {
    Log 'RESULT=FAIL'
    Log ("ERROR="+$_.Exception.Message)
    Write-Host ''
    Write-Host 'S0-C3 stopped safely. S0-A/S0-B/S0-C1/S0-C2 remain sealed.' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    Write-Host "Return log: $Log"
    Read-Host 'Press Enter to close'
    exit 1
}
Read-Host 'Press Enter to close'
