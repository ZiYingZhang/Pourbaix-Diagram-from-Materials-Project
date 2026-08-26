function Invoke-CheckedGuiProcess {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$ArgumentList = @()
    )

    if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf)) {
        throw "Windowed executable not found: $FilePath"
    }
    $Process = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -Wait -PassThru -WindowStyle Hidden
    if ($Process.ExitCode -ne 0) {
        throw "Windowed executable failed with exit code $($Process.ExitCode): $FilePath $($ArgumentList -join ' ')"
    }
}

function Remove-IncompatibleIcuDirectoriesFromPath {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)][string]$PathValue,
        [string]$SystemRootPath = $env:SystemRoot
    )

    $SystemPrefix = [IO.Path]::GetFullPath($SystemRootPath).TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    $KeptEntries = foreach ($Entry in $PathValue.Split([IO.Path]::PathSeparator)) {
        if ([string]::IsNullOrWhiteSpace($Entry)) {
            continue
        }
        try {
            $FullEntry = [IO.Path]::GetFullPath($Entry)
        } catch {
            $Entry
            continue
        }
        $IsSystemDirectory = $FullEntry.StartsWith($SystemPrefix, [StringComparison]::OrdinalIgnoreCase)
        $ContainsIcuRuntime = Test-Path -LiteralPath (Join-Path $FullEntry "icuuc.dll") -PathType Leaf
        if (-not $ContainsIcuRuntime -or $IsSystemDirectory) {
            $Entry
        }
    }
    return $KeptEntries -join [IO.Path]::PathSeparator
}

Export-ModuleMember -Function Invoke-CheckedGuiProcess, Remove-IncompatibleIcuDirectoriesFromPath

