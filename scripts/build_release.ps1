param(
    [string]$BuildRoot = "_build/R3.0",
    [string]$ReleaseRoot = "_release/R3.0",
    [switch]$ValidatePathsOnly,
    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))

function Resolve-SafeStagingPath {
    param(
        [Parameter(Mandatory = $true)][string]$Candidate,
        [Parameter(Mandatory = $true)][string]$RequiredTopLevel
    )

    $fullPath = if ([IO.Path]::IsPathRooted($Candidate)) {
        [IO.Path]::GetFullPath($Candidate)
    } else {
        [IO.Path]::GetFullPath((Join-Path $ProjectRoot $Candidate))
    }
    $projectPrefix = $ProjectRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if (
        $fullPath -eq $ProjectRoot -or
        -not $fullPath.StartsWith($projectPrefix, [StringComparison]::OrdinalIgnoreCase)
    ) {
        throw "Refusing unsafe staging path: $fullPath"
    }
    $relative = $fullPath.Substring($projectPrefix.Length)
    $topLevel = $relative.Split([IO.Path]::DirectorySeparatorChar)[0]
    if ($topLevel -ne $RequiredTopLevel -or $relative -eq $RequiredTopLevel) {
        throw "Refusing unsafe staging path: $fullPath"
    }
    return $fullPath
}

$ResolvedBuildRoot = Resolve-SafeStagingPath -Candidate $BuildRoot -RequiredTopLevel "_build"
$ResolvedReleaseRoot = Resolve-SafeStagingPath -Candidate $ReleaseRoot -RequiredTopLevel "_release"

if ($ValidatePathsOnly) {
    Write-Output "PATH-VALIDATION PASS"
    Write-Output "BuildRoot=$ResolvedBuildRoot"
    Write-Output "ReleaseRoot=$ResolvedReleaseRoot"
    exit 0
}

Set-Location -LiteralPath $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv-pourbaix-py313\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python 3.13 environment not found: $Python"
}

$GitStatus = (& git status --porcelain) -join "`n"
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read Git working-tree status."
}
if (-not $AllowDirty -and -not [string]::IsNullOrWhiteSpace($GitStatus)) {
    throw "Refusing reproducible release build from a dirty working tree. Commit intended changes first."
}

foreach ($PathToClean in @($ResolvedBuildRoot, $ResolvedReleaseRoot)) {
    if (Test-Path -LiteralPath $PathToClean) {
        Remove-Item -LiteralPath $PathToClean -Recurse -Force
    }
    New-Item -ItemType Directory -Path $PathToClean | Out-Null
}

$env:LOCALAPPDATA = Join-Path $ResolvedBuildRoot "local-app-data"
$env:MPLCONFIGDIR = Join-Path $ResolvedBuildRoot "matplotlib"
$env:QT_QPA_PLATFORM = "offscreen"

$TestOutput = & $Python -m pytest -q 2>&1
$TestExitCode = $LASTEXITCODE
$TestOutput | ForEach-Object { Write-Output $_ }
if ($TestExitCode -ne 0) {
    throw "Test suite failed with exit code $TestExitCode."
}
$TestText = $TestOutput -join "`n"
$PassedTests = 0
if ($TestText -match "(?m)(\d+) passed") {
    $PassedTests = [int]$Matches[1]
}

& $Python "pourbaix_gui_R3.py" --self-test
if ($LASTEXITCODE -ne 0) {
    throw "Source self-test failed with exit code $LASTEXITCODE."
}
& $Python "pourbaix_gui_R3.py" --gui-smoke
if ($LASTEXITCODE -ne 0) {
    throw "Source GUI smoke failed with exit code $LASTEXITCODE."
}

$LiveApiStatus = "Skipped"
$LiveApiReason = "No Materials Project API key was present in the process environment."
$ApiKeyAvailable = -not [string]::IsNullOrWhiteSpace($env:MP_API_KEY) -or -not [string]::IsNullOrWhiteSpace($env:MAPI_KEY) -or -not [string]::IsNullOrWhiteSpace($env:PMG_MAPI_KEY)
if ($ApiKeyAvailable) {
    & $Python "scripts\live_ti_smoke.py"
    if ($LASTEXITCODE -ne 0) {
        throw "Live Ti Materials Project smoke failed with exit code $LASTEXITCODE."
    }
    $LiveApiStatus = "Passed"
    $LiveApiReason = "A runtime environment key was available; the key value was not recorded."
}

& $Python -m PyInstaller --noconfirm --clean --workpath $ResolvedBuildRoot --distpath $ResolvedReleaseRoot "pourbaix_gui_R3.spec"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed with exit code $LASTEXITCODE."
}

$PackageDir = Join-Path $ResolvedReleaseRoot "pourbaix_gui_R3"
$PackageExe = Join-Path $PackageDir "pourbaix_gui_R3.exe"
if (-not (Test-Path -LiteralPath $PackageExe -PathType Leaf)) {
    throw "Packaged executable not found: $PackageExe"
}

foreach ($Doc in @("README.md", "USER_GUIDE.md", "THIRD_PARTY_NOTICES.md", "requirements-lock-py313-win64.txt")) {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot $Doc) -Destination (Join-Path $PackageDir $Doc)
}

& $PackageExe --self-test
if ($LASTEXITCODE -ne 0) {
    throw "Packaged self-test failed with exit code $LASTEXITCODE."
}
& $PackageExe --gui-smoke
if ($LASTEXITCODE -ne 0) {
    throw "Packaged GUI smoke failed with exit code $LASTEXITCODE."
}

$EntriesPayload = Get-ChildItem -LiteralPath $PackageDir -Recurse -Force -ErrorAction Stop |
    Where-Object { $_.Name -like "entries*" -and $_.FullName -match "pymatgen[\\/]core" } |
    Select-Object -First 1
if (-not $EntriesPayload) {
    throw "Packaged pymatgen/core/entries payload was not found."
}

$ForbiddenFiles = Get-ChildItem -LiteralPath $PackageDir -Recurse -Force -File |
    Where-Object { $_.Name -eq "mp_api_key.txt" -or $_.Extension -eq ".log" }
if ($ForbiddenFiles) {
    throw "Release package contains forbidden API-key or log files."
}

$ArchivePath = Join-Path $ResolvedReleaseRoot "pourbaix_gui_R3-win64.zip"
Compress-Archive -LiteralPath $PackageDir -DestinationPath $ArchivePath -CompressionLevel Optimal
if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf) -or (Get-Item -LiteralPath $ArchivePath).Length -eq 0) {
    throw "Release archive was not created or is empty."
}

$ExtractRoot = Join-Path $ResolvedBuildRoot "extracted"
New-Item -ItemType Directory -Path $ExtractRoot | Out-Null
Expand-Archive -LiteralPath $ArchivePath -DestinationPath $ExtractRoot
$ExtractedExe = Join-Path $ExtractRoot "pourbaix_gui_R3\pourbaix_gui_R3.exe"
if (-not (Test-Path -LiteralPath $ExtractedExe -PathType Leaf)) {
    throw "Extracted executable not found: $ExtractedExe"
}
& $ExtractedExe --self-test
if ($LASTEXITCODE -ne 0) {
    throw "Extracted packaged self-test failed with exit code $LASTEXITCODE."
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$Zip = [IO.Compression.ZipFile]::OpenRead($ArchivePath)
try {
    $ArchiveEntries = $Zip.Entries.Count
} finally {
    $Zip.Dispose()
}

$ArchiveItem = Get-Item -LiteralPath $ArchivePath
$ArchiveHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ArchivePath).Hash
$PackageFiles = (Get-ChildItem -LiteralPath $PackageDir -Recurse -Force -File | Measure-Object).Count
$SourceCommit = (& git rev-parse HEAD).Trim()
$PythonVersion = (& $Python --version 2>&1) -join " "
$PyInstallerVersion = (& $Python -m PyInstaller --version 2>&1) -join " "
$DependencyVersions = & $Python -c "import importlib.metadata as m, json; print(json.dumps({n:m.version(n) for n in ['mp-api','pymatgen','pymatgen-core','PyQt5','numpy','pandas','matplotlib','shapely','PyInstaller']}, sort_keys=True))"

$Manifest = [ordered]@{
    application_version = "R3.0"
    target_platform = "Windows x64"
    runtime_mode = "PyInstaller onedir"
    source_commit = $SourceCommit
    working_tree_dirty = -not [string]::IsNullOrWhiteSpace($GitStatus)
    build_timestamp_utc = [DateTime]::UtcNow.ToString("o")
    toolchain = [ordered]@{
        python = $PythonVersion
        pyinstaller = $PyInstallerVersion
        dependencies = ($DependencyVersions | ConvertFrom-Json)
    }
    tests = [ordered]@{
        status = "Passed"
        passed = $PassedTests
        failed = 0
        skipped = 0
    }
    smokes = [ordered]@{
        source_self_test = 0
        source_gui = 0
        packaged_self_test = 0
        packaged_gui = 0
        extracted_self_test = 0
    }
    live_materials_project_ti = [ordered]@{
        status = $LiveApiStatus
        reason = $LiveApiReason
    }
    package = [ordered]@{
        directory = "pourbaix_gui_R3"
        files = $PackageFiles
        pymatgen_core_entries = $EntriesPayload.FullName.Substring($PackageDir.Length).TrimStart("\")
        forbidden_files = 0
    }
    archive = [ordered]@{
        name = $ArchiveItem.Name
        bytes = $ArchiveItem.Length
        entries = $ArchiveEntries
        sha256 = $ArchiveHash
    }
    external_acceptance = [ordered]@{
        status = "Pending"
        required_environment = "Separate clean Windows x64 machine without Python, using this exact archive SHA-256."
    }
}

$ManifestPath = Join-Path $ResolvedReleaseRoot "release-manifest.json"
$Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $ManifestPath -Encoding UTF8
Write-Output "RELEASE-BUILD PASS"
Write-Output "Archive=$ArchivePath"
Write-Output "SHA256=$ArchiveHash"
Write-Output "Manifest=$ManifestPath"
