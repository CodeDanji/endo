$ErrorActionPreference = 'Stop'

try {
    Write-Host "Reading python script..."
    $code = [IO.File]::ReadAllText("C:\Users\권원중학부재학바이오의공학부\Desktop\ENDO\src\build_endocrab_model\build_p1_skeleton.py")
    $bodyObj = @{ code = $code }
    $body = $bodyObj | ConvertTo-Json -Depth 10

    Write-Host "Triggering execute_code endpoint..."
    $res = Invoke-RestMethod -Uri "http://localhost:8080/execute_code" -Method Post -Body $body -ContentType "application/json"
    
    Start-Sleep -Seconds 2

    Write-Host "Getting inspect state..."
    $inspectRes = Invoke-RestMethod -Uri "http://localhost:8080/inspect" -Method Get
    
    Write-Host "State:"
    $inspectRes.state | ConvertTo-Json -Depth 10 | Write-Host
    
    if ($inspectRes.image_b64) {
        $bytes = [Convert]::FromBase64String($inspectRes.image_b64)
        [IO.File]::WriteAllBytes("C:\Users\권원중학부재학바이오의공학부\Desktop\ENDO\output_skeleton.png", $bytes)
        Write-Host "Image saved to output_skeleton.png"
    }
} catch {
    Write-Host "Error occurred: $_"
}
