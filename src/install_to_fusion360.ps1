# Auto-Deployment Script for Fusion 360 Add-Ins, Scripts and MCP Server Setup

$AddInTarget = "$env:APPDATA\Autodesk\Autodesk Fusion 360\API\AddIns\AntigravityOnDemand"
$ScriptTarget = "$env:APPDATA\Autodesk\Autodesk Fusion 360\API\Scripts\ENDOCRAB_Builder"

$SourceBase = "C:\Users\권원중학부재학바이오의공학부\Desktop\ENDO\src"

Write-Host "Deploying AntigravityOnDemand Add-in..." -ForegroundColor Cyan
if (!(Test-Path $AddInTarget)) {
    New-Item -ItemType Directory -Path $AddInTarget -Force | Out-Null
}
Copy-Item "$SourceBase\AntigravityOnDemand\*" -Destination $AddInTarget -Recurse -Force

# Purge __pycache__ in AddInTarget
Get-ChildItem -Path $AddInTarget -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $AddInTarget -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Add-In installed to: $AddInTarget" -ForegroundColor Green

Write-Host "`nDeploying ENDOCRAB_Builder Script..." -ForegroundColor Cyan
if (!(Test-Path $ScriptTarget)) {
    New-Item -ItemType Directory -Path $ScriptTarget -Force | Out-Null
}
Copy-Item "$SourceBase\ENDOCRAB_Builder\*" -Destination $ScriptTarget -Recurse -Force
Copy-Item "$SourceBase\build_endocrab_model.py" -Destination $ScriptTarget -Force

# Purge __pycache__ in ScriptTarget
Get-ChildItem -Path $ScriptTarget -Recurse -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path $ScriptTarget -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Script installed to: $ScriptTarget" -ForegroundColor Green

Write-Host "`n=======================================================" -ForegroundColor Yellow
Write-Host "Fusion 360 MCP Server Configuration Guide" -ForegroundColor Yellow
Write-Host "=======================================================" -ForegroundColor Yellow
Write-Host "Claude Desktop / Cursor / Antigravity JSON config:" -ForegroundColor White
$ProjectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$McpScript = Join-Path $PSScriptRoot "fusion360_mcp_server.py"
$EscapedPython = $VenvPython.Replace('\', '\\')
$EscapedScript = $McpScript.Replace('\', '\\')

Write-Host @"
{
  "mcpServers": {
    "fusion360": {
      "command": "$EscapedPython",
      "args": ["$EscapedScript"]
    }
  }
}
"@ -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Yellow

Write-Host "`nInstallation & Deployment Completed Successfully!" -ForegroundColor Yellow
