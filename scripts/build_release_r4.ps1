param(
    [string]$BuildRoot = "_build/R4.0",
    [string]$ReleaseRoot = "_release/R4.0",
    [string]$PythonPath = "",
    [switch]$ValidatePathsOnly,
    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"
$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Import-Module (Join-Path $PSScriptRoot "release_helpers.psm1") -Force

function Resolve-SafeStagingPath {
    param(
        [Parameter(Mandatory = $true)][string]$Candidate,
        [Parameter(Mandatory = $true)][string]$RequiredTopLevel
    )

    $FullPath = if ([IO.Path]::IsPathRooted($Candidate)) {
        [IO.Path]::GetFullPath($Candidate)
    } else {
        [IO.Path]::GetFullPath((Join-Path $ProjectRoot $Candidate))
    }
    $ProjectPrefix = $ProjectRoot.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if ($FullPath -eq $ProjectRoot -or -not $FullPath.StartsWith($ProjectPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing unsafe staging path: $FullPath"
    }
    $Relative = $FullPath.Substring($ProjectPrefix.Length)
    $TopLevel = $Relative.Split([IO.Path]::DirectorySeparatorChar)[0]
    if ($TopLevel -ne $RequiredTopLevel -or $Relative -eq $RequiredTopLevel) {
        throw "Refusing unsafe staging path: $FullPath"
    }
    return $FullPath
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
$Python = if ([string]::IsNullOrWhiteSpace($PythonPath)) {
    Join-Path $ProjectRoot ".venv-pourbaix-py313\Scripts\python.exe"
} elseif ([IO.Path]::IsPathRooted($PythonPath)) {
    [IO.Path]::GetFullPath($PythonPath)
} else {
    [IO.Path]::GetFullPath((Join-Path $ProjectRoot $PythonPath))
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python 3.13 environment not found: $Python"
}

$SourcePngIcon = Join-Path $ProjectRoot "assets\pourbaix-studio-r4.png"
$SourceWindowsIcon = Join-Path $ProjectRoot "assets\pourbaix-studio-r4.ico"
foreach ($IconAsset in @($SourcePngIcon, $SourceWindowsIcon)) {
    if (-not (Test-Path -LiteralPath $IconAsset -PathType Leaf)) {
        throw "Required application icon was not found: $IconAsset"
    }
}

$GitStatus = (& git status --porcelain) -join "`n"
if ($LASTEXITCODE -ne 0) {
    throw "Unable to read Git working-tree status."
}
if (-not $AllowDirty -and -not [string]::IsNullOrWhiteSpace($GitStatus)) {
    throw "Refusing reproducible release build from a dirty working tree. Commit intended changes first or use -AllowDirty for a local candidate."
}

foreach ($PathToClean in @($ResolvedBuildRoot, $ResolvedReleaseRoot)) {
    if (Test-Path -LiteralPath $PathToClean) {
        Remove-Item -LiteralPath $PathToClean -Recurse -Force
    }
    New-Item -ItemType Directory -Path $PathToClean | Out-Null
}

$env:LOCALAPPDATA = Join-Path $ResolvedBuildRoot "local-app-data"
$env:MPLCONFIGDIR = Join-Path $ResolvedBuildRoot "matplotlib"
$env:TEMP = Join-Path $ResolvedBuildRoot "temp"
$env:TMP = $env:TEMP
$env:QT_QPA_PLATFORM = "offscreen"
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null

$TestOutput = & $Python -m pytest -q "tests/r4" 2>&1
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

& $Python "pourbaix_studio_R4.py" --self-test
if ($LASTEXITCode -ne 0) {
    throw "R4 source self-test failed with exit code $LASTEXITCODE."
}
& $Python "pourbaix_studio_R4.py" --gui-smoke
if ($LASTEXITCODE -ne 0) {
    throw "R4 source GUI smoke failed with exit code $LASTEXITCODE."
}
& $Python "pourbaix_studio_R4.py" --mpcontribs-smoke
if ($LASTEXITCODE -ne 0) {
    throw "R4 source MPContribs smoke failed with exit code $LASTEXITCODE."
}

$OriginalBuildPath = $env:PATH
$env:PATH = Remove-IncompatibleIcuDirectoriesFromPath -PathValue $OriginalBuildPath
if ($env:PATH -ne $OriginalBuildPath) {
    Write-Output "Removed non-system ICU directories from the PyInstaller PATH."
}

& $Python -m PyInstaller --noconfirm --clean --workpath $ResolvedBuildRoot --distpath $ResolvedReleaseRoot "pourbaix_studio_R4.spec"
if ($LASTEXITCODE -ne 0) {
    throw "R4 PyInstaller build failed with exit code $LASTEXITCODE."
}

$PackageDir = Join-Path $ResolvedReleaseRoot "PourbaixStudioR4"
$PackageExe = Join-Path $PackageDir "PourbaixStudioR4.exe"
if (-not (Test-Path -LiteralPath $PackageExe -PathType Leaf)) {
    throw "Packaged R4 executable not found: $PackageExe"
}
$PackagedRuntimeIcon = Join-Path $PackageDir "_internal\assets\pourbaix-studio-r4.png"
if (-not (Test-Path -LiteralPath $PackagedRuntimeIcon -PathType Leaf)) {
    throw "Packaged runtime icon was not found: $PackagedRuntimeIcon"
}
$PackagedRfc3987Grammar = Join-Path $PackageDir "_internal\rfc3987_syntax\syntax_rfc3987.lark"
if (-not (Test-Path -LiteralPath $PackagedRfc3987Grammar -PathType Leaf)) {
    throw "Packaged MPContribs parser grammar was not found: $PackagedRfc3987Grammar"
}

foreach ($Doc in @("README.md", "USER_GUIDE.md", "THIRD_PARTY_NOTICES.md", "requirements-lock-py313-win64-r4.txt")) {
    Copy-Item -LiteralPath (Join-Path $ProjectRoot $Doc) -Destination (Join-Path $PackageDir $Doc)
}

Invoke-CheckedGuiProcess -FilePath $PackageExe -ArgumentList @("--self-test")
Invoke-CheckedGuiProcess -FilePath $PackageExe -ArgumentList @("--gui-smoke")
Invoke-CheckedGuiProcess -FilePath $PackageExe -ArgumentList @("--mpcontribs-smoke")

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

$ArchivePath = Join-Path $ResolvedReleaseRoot "PourbaixStudioR4-win64.zip"
Compress-Archive -LiteralPath $PackageDir -DestinationPath $ArchivePath -CompressionLevel Optimal
if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf) -or (Get-Item -LiteralPath $ArchivePath).Length -eq 0) {
    throw "R4 release archive was not created or is empty."
}

$ExtractRoot = Join-Path $ResolvedBuildRoot "extracted"
New-Item -ItemType Directory -Path $ExtractRoot | Out-Null
Expand-Archive -LiteralPath $ArchivePath -DestinationPath $ExtractRoot
$ExtractedExe = Join-Path $ExtractRoot "PourbaixStudioR4\PourbaixStudioR4.exe"
if (-not (Test-Path -LiteralPath $ExtractedExe -PathType Leaf)) {
    throw "Extracted R4 executable not found: $ExtractedExe"
}
Invoke-CheckedGuiProcess -FilePath $ExtractedExe -ArgumentList @("--self-test")
Invoke-CheckedGuiProcess -FilePath $ExtractedExe -ArgumentList @("--gui-smoke")
Invoke-CheckedGuiProcess -FilePath $ExtractedExe -ArgumentList @("--mpcontribs-smoke")

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
$DependencyVersions = & $Python -c "import importlib.metadata as m, json; print(json.dumps({n:m.version(n) for n in ['mp-api','pymatgen','pymatgen-core','PySide6','keyring','numpy','pandas','matplotlib','shapely','PyInstaller']}, sort_keys=True))"

$Manifest = [ordered]@{
    application_version = "R4.0"
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
    tests = [ordered]@{ status = "Passed"; passed = $PassedTests; failed = 0; skipped = 0 }
    smokes = [ordered]@{
        source_self_test = 0
        source_gui = 0
        source_mpcontribs = 0
        packaged_self_test = 0
        packaged_gui = 0
        packaged_mpcontribs = 0
        extracted_self_test = 0
        extracted_gui = 0
        extracted_mpcontribs = 0
    }
    live_materials_project = [ordered]@{
        status = "Skipped"
        reason = "Release builds never use a user's API key automatically."
    }
    package = [ordered]@{
        directory = "PourbaixStudioR4"
        files = $PackageFiles
        pymatgen_core_entries = $EntriesPayload.FullName.Substring($PackageDir.Length).TrimStart("\")
        runtime_icon = $PackagedRuntimeIcon.Substring($PackageDir.Length).TrimStart("\")
        mpcontribs_grammar = $PackagedRfc3987Grammar.Substring($PackageDir.Length).TrimStart("\")
        forbidden_files = 0
    }
    branding = [ordered]@{
        repository = "https://github.com/ZiYingZhang/Pourbaix-Diagram-from-Materials-Project"
        source_png = "assets/pourbaix-studio-r4.png"
        windows_icon = "assets/pourbaix-studio-r4.ico"
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
Write-Output "R4 RELEASE-BUILD PASS"
Write-Output "Archive=$ArchivePath"
Write-Output "SHA256=$ArchiveHash"
Write-Output "Manifest=$ManifestPath"
