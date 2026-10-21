param([Parameter(Mandatory=$true)][string]$Name, [string]$Program, [switch]$Remove)
$ErrorActionPreference = 'Stop'
if ($Remove) {
    Get-NetFirewallRule -DisplayName $Name | Remove-NetFirewallRule
} else {
    New-NetFirewallRule -DisplayName $Name -Direction Outbound -Action Block -Profile Any -Program $Program | Out-Null
}
