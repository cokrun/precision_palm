$ErrorActionPreference = "Continue"
$project = "palm-project-511008"
$region = "asia-southeast2"
$baseUrl = "https://precision-palm-739036785917.asia-southeast2.run.app"

Write-Host "=== 1. VERIFIKASI BIGQUERY DATASET & TABEL ===" -ForegroundColor Cyan
bq ls --project_id=$project precision_palm_dw

Write-Host "`n=== 2. VERIFIKASI KESEHATAN ENDPOINT CLOUD RUN ===" -ForegroundColor Cyan
$endpoints = @("/", "/roadmap", "/spatial", "/mobile", "/topologi", "/api/estates")
foreach ($ep in $endpoints) {
    try {
        $res = Invoke-WebRequest -Uri "$baseUrl$ep" -Method Get -UseBasicParsing -TimeoutSec 15
        Write-Host "[$($res.StatusCode)] $ep" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] $ep -> $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n=== 3. VERIFIKASI PERSISTENCE REVIEW & DATA DUAL-WRITE ===" -ForegroundColor Cyan
try {
    $reviewTest = Invoke-RestMethod -Uri "$baseUrl/api/ai/get-node-review?node_id=NODE-01&estate_code=EST-MDN-001" -Method Get -TimeoutSec 15
    Write-Host "Status Response GET Review: Success" -ForegroundColor Green
    $reviewTest | ConvertTo-Json -Depth 2 | Write-Host
} catch {
    Write-Host "Review belum tersimpan atau endpoint error: $($_.Exception.Message)" -ForegroundColor Yellow
}
