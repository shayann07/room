[CmdletBinding(SupportsShouldProcess)]
param(
    [ValidateSet('all', 'claude', 'codex', 'antigravity')]
    [string]$Provider = 'all'
)

$ErrorActionPreference = 'Stop'
$roomRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = (Get-Command python).Source
$db = Join-Path $roomRoot 'artifacts\m0\registered-room.sqlite3'

$commands = @{
    claude = @('claude', @('mcp', 'add', '--scope', 'local', 'room-m0', '--', $python, (Join-Path $roomRoot 'room_mcp.py'), '--db', $db, '--store', 'sqlite', '--participant', 'claude'))
    codex = @('codex', @('mcp', 'add', 'room-m0', '--', $python, (Join-Path $roomRoot 'room_mcp.py'), '--db', $db, '--store', 'sqlite', '--participant', 'codex'))
    antigravity = @('agy', @('mcp', 'add', 'room-m0', $python, (Join-Path $roomRoot 'room_mcp.py'), '--db', $db, '--store', 'sqlite', '--participant', 'antigravity'))
}

$providers = if ($Provider -eq 'all') { @('claude', 'codex', 'antigravity') } else { @($Provider) }
foreach ($name in $providers) {
    $executable = $commands[$name][0]
    $arguments = $commands[$name][1]
    $display = "$executable $($arguments -join ' ')"
    if ($PSCmdlet.ShouldProcess("$name MCP configuration", "Register room-m0 using $display")) {
        & $executable @arguments
        if ($LASTEXITCODE -ne 0) {
            throw "$name registration failed with exit code $LASTEXITCODE"
        }
    } else {
        Write-Output "WHATIF: $display"
    }
}
