#!/usr/bin/env pwsh
# Setup multiple Ollama models for cost optimization testing

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  ASTRA AI - Multi-Model Setup for Cost Testing" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Ollama is installed
Write-Host "🔍 Step 1: Checking Ollama installation..." -ForegroundColor Cyan
try {
    $version = ollama --version 2>&1
    Write-Host "✅ Ollama is installed: $version" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "❌ ERROR: Ollama is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install from: https://ollama.com/download" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}

# Model configurations for cost testing
$models = @(
    @{
        Name = "llama3:latest"
        Description = "LLaMA 3 - Best quality, larger size"
        Size = "~4.7 GB"
        Speed = "Medium"
        Quality = "Excellent"
        CostRatio = 1.0
    },
    @{
        Name = "mistral:latest"
        Description = "Mistral 7B - Balanced performance"
        Size = "~4.1 GB"
        Speed = "Fast"
        Quality = "Very Good"
        CostRatio = 0.8
    },
    @{
        Name = "phi3:latest"
        Description = "Phi-3 Mini - Fastest, smallest"
        Size = "~2.3 GB"
        Speed = "Very Fast"
        Quality = "Good"
        CostRatio = 0.5
    }
)

Write-Host "📋 Models to download for cost optimization testing:" -ForegroundColor Cyan
Write-Host ""
foreach ($model in $models) {
    Write-Host "  📦 $($model.Name)" -ForegroundColor Yellow
    Write-Host "     - $($model.Description)" -ForegroundColor White
    Write-Host "     - Size: $($model.Size) | Speed: $($model.Speed) | Quality: $($model.Quality)" -ForegroundColor DarkGray
    Write-Host "     - Cost Ratio: $($model.CostRatio)x (relative to LLaMA 3)" -ForegroundColor DarkGray
    Write-Host ""
}

Write-Host "⏱️  Estimated total time: 15-20 minutes (depending on internet speed)" -ForegroundColor Yellow
Write-Host "💾 Total disk space needed: ~11 GB" -ForegroundColor Yellow
Write-Host ""

# Ask for confirmation
Write-Host "Do you want to proceed? (Y/N): " -ForegroundColor Cyan -NoNewline
$response = Read-Host
if ($response -ne 'Y' -and $response -ne 'y') {
    Write-Host ""
    Write-Host "❌ Cancelled by user" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "🚀 Starting model downloads..." -ForegroundColor Green
Write-Host ""

# Download each model
$downloadedModels = @()
foreach ($model in $models) {
    Write-Host "=====================================================" -ForegroundColor DarkGray
    Write-Host "📥 Downloading: $($model.Name)" -ForegroundColor Yellow
    Write-Host "   $($model.Description)" -ForegroundColor White
    Write-Host "=====================================================" -ForegroundColor DarkGray
    Write-Host ""
    
    try {
        ollama pull $model.Name
        Write-Host ""
        Write-Host "✅ Successfully downloaded: $($model.Name)" -ForegroundColor Green
        $downloadedModels += $model.Name
        Write-Host ""
        Start-Sleep -Seconds 2
    } catch {
        Write-Host ""
        Write-Host "❌ Failed to download: $($model.Name)" -ForegroundColor Red
        Write-Host "   Error: $_" -ForegroundColor DarkRed
        Write-Host ""
    }
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  ✅ Setup Complete!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""

# List all downloaded models
Write-Host "📋 Verifying installed models..." -ForegroundColor Cyan
Write-Host ""
ollama list
Write-Host ""

# Summary
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  📊 Cost Optimization Setup Summary" -ForegroundColor Yellow
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Downloaded models: $($downloadedModels.Count)/$($models.Count)" -ForegroundColor Green
Write-Host ""

foreach ($modelName in $downloadedModels) {
    $modelInfo = $models | Where-Object { $_.Name -eq $modelName }
    Write-Host "✅ $modelName" -ForegroundColor Green
    Write-Host "   Speed: $($modelInfo.Speed) | Quality: $($modelInfo.Quality) | Cost: $($modelInfo.CostRatio)x" -ForegroundColor DarkGray
    Write-Host ""
}

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Test individual models:" -ForegroundColor White
Write-Host "   ollama run llama3 'Hello!'" -ForegroundColor DarkGray
Write-Host "   ollama run mistral 'Hello!'" -ForegroundColor DarkGray
Write-Host "   ollama run phi3 'Hello!'" -ForegroundColor DarkGray
Write-Host ""
Write-Host "2. Run the verification script:" -ForegroundColor White
Write-Host "   python test_ollama.py" -ForegroundColor DarkGray
Write-Host ""
Write-Host "3. Test ASTRA AI with cost optimization:" -ForegroundColor White
Write-Host "   python main.py --interactive" -ForegroundColor DarkGray
Write-Host ""
Write-Host "💡 The system will automatically choose the best model based on:" -ForegroundColor Cyan
Write-Host "   - Quality requirements" -ForegroundColor DarkGray
Write-Host "   - Speed needs" -ForegroundColor DarkGray
Write-Host "   - Cost constraints" -ForegroundColor DarkGray
Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
