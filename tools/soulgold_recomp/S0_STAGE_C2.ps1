param(
    [string]$EvidenceRoot = "$env:USERPROFILE\SoulGoldRecomp_S0\_evidence"
)

$ErrorActionPreference='Stop'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
New-Item -ItemType Directory -Force -Path $EvidenceRoot | Out-Null
$Log=Join-Path $EvidenceRoot ("S0_STAGE_C2_{0}.log" -f $Stamp)

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
  } finally {
    $ErrorActionPreference=$old
  }
  if($rc -ne 0){
    throw "WSL failed ($rc): $($CommandArgs -join ' ') :: $($x -join ' | ')"
  }
  if($x.Count -eq 0){return ''}
  return (($x|Select-Object -Last 1).ToString()).Trim()
}
function Stream([string]$label,[string[]]$CommandArgs) {
  $old=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    & wsl.exe @CommandArgs 2>&1 | ForEach-Object { Log "$label $_" }
    $rc=$LASTEXITCODE
  } finally {
    $ErrorActionPreference=$old
  }
  if($rc -ne 0){throw "$label failed ($rc)"}
}
function Exists([string]$p) {
  $old=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    & wsl.exe test -e $p 2>$null
    $rc=$LASTEXITCODE
  } finally {
    $ErrorActionPreference=$old
  }
  return $rc -eq 0
}
function WinToWsl([string]$p) {
  $full=(Resolve-Path $p).Path
  if($full -notmatch '^([A-Za-z]):\\(.*)$'){
    throw "Unsupported Windows path: $full"
  }
  $d=$Matches[1].ToLowerInvariant()
  $r=$Matches[2].Replace([char]92,[char]47)
  return "/mnt/$d/$r"
}

try {
  Log 'S0_STAGE_C2_BEGIN'

  # IMPORTANT: PowerShell automatic variable $HOME is case-insensitive.
  # Never assign to $home/$Home. Use a distinct variable name.
  $WslHomePath=Scalar @('python3','-c','from pathlib import Path; print(Path.home())')
  if(-not $WslHomePath.StartsWith('/')){
    throw "Unexpected WSL HOME path: $WslHomePath"
  }
  Log "WSL_HOME_PATH=$WslHomePath"

  $ws="$WslHomePath/SoulGoldRecomp_S0"
  $sg="$ws/soulgold"
  $gb="$ws/gbarecomp"
  $rr="$ws/SoulGoldRecomp"
  $runner="$rr/build-s0/SoulGoldRecomp"
  $rom="$sg/Soulgold_Beta_1.gba"
  $bios="$gb/bios/gba_bios.bin"
  $config="$rr/variants/soulgold/game.toml"
  $runDir="$ws/_s0c2"
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

  $trace="$runDir/start_press.trace"
  $traceText="# gbarecomp-keyinput-v1`n# frame,keyinput_active_low`n0,0x03FF`n1250,0x03F7`n1270,0x03FF`n"
  $traceWin=Join-Path $EvidenceRoot ("S0C2_start_press_$Stamp.trace")
  $traceText | Set-Content -Path $traceWin -Encoding ASCII
  $traceMount=WinToWsl $traceWin
  Stream 'TRACE[COPY]' @('cp',$traceMount,$trace)
  Log 'INPUT_START_PRESS=frame1250..1269 active_low=0x03F7'

  $png1600="$runDir/S0C2_frame1600_$Stamp.png"
  $png3000="$runDir/S0C2_frame3000_$Stamp.png"
  $cov="$runDir/S0C2_coverage_$Stamp.json"
  $miss="$runDir/S0C2_misses_$Stamp.toml.frag"

  Log 'STEP=RUN_TO_1600'
  $old=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    & wsl.exe env "GBARECOMP_INPUT_REPLAY=$trace" $runner --config $config --bios $bios --rom $rom --bios-hle --no-window --frames 1600 --dump-png $png1600 2>&1 |
      ForEach-Object { Log "RUN1600 $_" }
    $rc1=$LASTEXITCODE
  } finally {
    $ErrorActionPreference=$old
  }
  Log "RUN1600_EXIT=$rc1"
  if($rc1 -ne 0 -or -not (Exists $png1600)){
    throw "1600-frame replay failed rc=$rc1"
  }

  Log 'STEP=RUN_TO_3000'
  $old=$ErrorActionPreference
  try {
    $ErrorActionPreference='Continue'
    & wsl.exe env "GBARECOMP_INPUT_REPLAY=$trace" "GBARECOMP_COVERAGE_JSON=$cov" "GBARECOMP_MISS_FRAG=$miss" $runner --config $config --bios $bios --rom $rom --bios-hle --no-window --frames 3000 --dump-png $png3000 2>&1 |
      ForEach-Object { Log "RUN3000 $_" }
    $rc2=$LASTEXITCODE
  } finally {
    $ErrorActionPreference=$old
  }
  Log "RUN3000_EXIT=$rc2"
  if($rc2 -ne 0 -or -not (Exists $png3000)){
    throw "3000-frame replay failed rc=$rc2"
  }

  $evWsl=WinToWsl $EvidenceRoot
  $p1Local=Join-Path $EvidenceRoot ("S0C2_frame1600_$Stamp.png")
  $p2Local=Join-Path $EvidenceRoot ("S0C2_frame3000_$Stamp.png")
  Stream 'COPY[1600]' @('cp',$png1600,"$evWsl/S0C2_frame1600_$Stamp.png")
  Stream 'COPY[3000]' @('cp',$png3000,"$evWsl/S0C2_frame3000_$Stamp.png")

  $covLocal=Join-Path $EvidenceRoot ("S0C2_coverage_$Stamp.json")
  $missLocal=Join-Path $EvidenceRoot ("S0C2_misses_$Stamp.toml.frag")
  if(Exists $cov){
    Stream 'COPY[COV]' @('cp',$cov,"$evWsl/S0C2_coverage_$Stamp.json")
  }
  if(Exists $miss){
    Stream 'COPY[MISS]' @('cp',$miss,"$evWsl/S0C2_misses_$Stamp.toml.frag")
  }

  $authority=Join-Path $EvidenceRoot 'S0_C2_CANDIDATE_AUTHORITY.txt'
  @(
    'SOULGOLDRECOMP S0-C2 CANDIDATE AUTHORITY',
    'RESULT=CANDIDATE_PASS',
    "RUNNER_SHA256=$rsha",
    "ROM_SHA1=$romsha",
    "BIOS_SHA1=$biossha",
    'INPUT=START frame1250-1269 active-low 0x03F7',
    'CHECKPOINT_1=1600 frames',
    'CHECKPOINT_2=3000 frames',
    "FRAME_1600=$p1Local",
    "FRAME_3000=$p2Local",
    'FORMAL_PASS=REQUIRES_FRAMEBUFFER_REVIEW',
    'NEXT_IF_TITLE_HEALTHY=S0-C3_INTERACTIVE_RUNTIME'
  )|Set-Content -Path $authority -Encoding UTF8

  Log 'RESULT=CANDIDATE_PASS'
  $zip=Join-Path $EvidenceRoot ("SOULGOLD_S0_C2_EVIDENCE_{0}.zip" -f $Stamp)
  $files=@($Log,$authority,$traceWin,$p1Local,$p2Local)
  if(Test-Path $covLocal){$files+=$covLocal}
  if(Test-Path $missLocal){$files+=$missLocal}
  Compress-Archive -Path $files -DestinationPath $zip -Force

  Write-Host ''
  Write-Host 'S0-C2 CANDIDATE PASS. START was replayed through the real input path.' -ForegroundColor Green
  Write-Host 'Return the evidence ZIP; framebuffer review decides formal promotion.' -ForegroundColor Yellow
  Write-Host "Evidence ZIP: $zip"
}
catch {
  Log 'RESULT=FAIL'
  Log ("ERROR="+$_.Exception.Message)
  Write-Host ''
  Write-Host 'S0-C2 stopped safely. S0-A/S0-B/S0-C1 remain sealed.' -ForegroundColor Red
  Write-Host $_.Exception.Message -ForegroundColor Yellow
  Write-Host "Return log: $Log"
  Read-Host 'Press Enter to close'
  exit 1
}
Read-Host 'Press Enter to close'
