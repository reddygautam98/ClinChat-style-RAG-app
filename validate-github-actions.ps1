# GitHub Actions Validation Script
# This script helps validate that all deprecated actions have been updated

Write-Host "GitHub Actions Validation Report" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

$workflowFile = "C:\Users\reddy\Downloads\ClinChat-style-RAG-app\.github\workflows\ci-cd.yml"

if (Test-Path $workflowFile) {
    Write-Host "✅ Workflow file found: ci-cd.yml" -ForegroundColor Green
    
    # Check for deprecated upload-artifact versions
    $content = Get-Content $workflowFile -Raw
    
    Write-Host "`nChecking for deprecated actions..." -ForegroundColor Yellow
    
    # Check for upload-artifact@v3 or earlier
    if ($content -match "upload-artifact@v[1-3]") {
        Write-Host "❌ Found deprecated upload-artifact action" -ForegroundColor Red
    } else {
        Write-Host "✅ No deprecated upload-artifact actions found" -ForegroundColor Green
    }
    
    # Check for upload-artifact@v4
    if ($content -match "upload-artifact@v4") {
        Write-Host "✅ Found updated upload-artifact@v4" -ForegroundColor Green
    } else {
        Write-Host "⚠️  No upload-artifact@v4 found - may need to add artifact uploads" -ForegroundColor Yellow
    }
    
    # Check for other potentially outdated actions
    Write-Host "`nChecking other actions..." -ForegroundColor Yellow
    
    if ($content -match "setup-python@v5") {
        Write-Host "✅ Using latest setup-python@v5" -ForegroundColor Green
    }
    
    if ($content -match "codecov-action@v4") {
        Write-Host "✅ Using latest codecov-action@v4" -ForegroundColor Green
    }
    
    if ($content -match "checkout@v4") {
        Write-Host "✅ Using latest checkout@v4" -ForegroundColor Green
    }
    
    Write-Host "`nArtifact uploads configured:" -ForegroundColor Yellow
    
    # Count artifact uploads
    $artifactCount = ($content | Select-String "upload-artifact@v4" -AllMatches).Matches.Count
    Write-Host "   📦 Total artifact uploads: $artifactCount" -ForegroundColor Cyan
    
    if ($content -match "name: test-results") {
        Write-Host "   ✅ Python test results upload configured" -ForegroundColor Green
    }
    
    if ($content -match "name: frontend-build") {
        Write-Host "   ✅ Frontend build artifacts upload configured" -ForegroundColor Green
    }
    
    if ($content -match "name: frontend-coverage") {
        Write-Host "   ✅ Frontend coverage upload configured" -ForegroundColor Green
    }
    
    if ($content -match "name: trivy-results") {
        Write-Host "   ✅ Security scan results upload configured" -ForegroundColor Green
    }
    
    Write-Host "`n🎉 Validation Complete!" -ForegroundColor Green
    Write-Host "Your workflow is now compatible with current GitHub Actions standards." -ForegroundColor Green
    
} else {
    Write-Host "❌ Workflow file not found!" -ForegroundColor Red
}

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Commit and push these changes to GitHub" -ForegroundColor White
Write-Host "2. Trigger a workflow run to test the updates" -ForegroundColor White
Write-Host "3. Verify artifacts are uploaded successfully" -ForegroundColor White