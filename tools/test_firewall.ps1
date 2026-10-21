param([Parameter(Mandatory=$true)][string]$Name, [string]$Program, [switch]$Remove)
$ErrorActionPreference = 'Stop'
if ($Remove) {
    Get-NetFirewallRule -DisplayName $Name | Remove-NetFirewallRule
} else {
    if (-not (Test-Path -LiteralPath $Program -PathType Leaf)) {
        throw 'The firewall test executable does not exist.'
    }
    New-NetFirewallRule -DisplayName $Name -Direction Outbound -Action Block -Profile Any -Program $Program -Enabled True | Out-Null
}
