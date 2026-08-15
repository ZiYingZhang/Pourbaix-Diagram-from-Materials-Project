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

Export-ModuleMember -Function Invoke-CheckedGuiProcess

