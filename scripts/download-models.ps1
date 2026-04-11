# LocalMind Model Downloader
# Downloads all evaluation models to the models/ directory
# Run from repo root: powershell -ExecutionPolicy Bypass -File scripts\download-models.ps1

$dest = "$PSScriptRoot\..\models"
$dest = (Resolve-Path $dest).Path

$downloads = @(
    @{
        url  = "https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/resolve/main/gemma-4-E4B-it-UD-IQ3_XXS.gguf"
        file = "gemma-4-E4B-it-UD-IQ3_XXS.gguf"
        size = "3.7 GB"
    },
    @{
        url  = "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-IQ4_XS.gguf"
        file = "gemma-4-E2B-it-IQ4_XS.gguf"
        size = "2.98 GB"
    },
    @{
        url  = "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/gemma-4-E2B-it-UD-IQ3_XXS.gguf"
        file = "gemma-4-E2B-it-UD-IQ3_XXS.gguf"
        size = "2.37 GB"
    },
    @{
        url  = "https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/resolve/main/mmproj-F16.gguf"
        file = "mmproj-E4B-F16.gguf"
        size = "~600 MB"
    },
    @{
        url  = "https://huggingface.co/unsloth/gemma-4-E2B-it-GGUF/resolve/main/mmproj-F16.gguf"
        file = "mmproj-E2B-F16.gguf"
        size = "~600 MB"
    }
)

Write-Host "`nLocalMind Model Downloader" -ForegroundColor Cyan
Write-Host "Destination: $dest`n"

foreach ($d in $downloads) {
    $outPath = Join-Path $dest $d.file

    if (Test-Path $outPath) {
        $existing = (Get-Item $outPath).Length
        Write-Host "  [SKIP] $($d.file) already exists ($([math]::Round($existing/1GB,2)) GB)" -ForegroundColor Yellow
        continue
    }

    Write-Host "  Downloading $($d.file) ($($d.size))..." -ForegroundColor Green

    try {
        # Use WebClient for progress + redirect support
        $wc = New-Object System.Net.WebClient
        $wc.Headers.Add("User-Agent", "Mozilla/5.0")

        # Track progress
        $job = $null
        Register-ObjectEvent $wc DownloadProgressChanged -Action {
            $pct = $Event.SourceEventArgs.ProgressPercentage
            $mb  = [math]::Round($Event.SourceEventArgs.BytesReceived / 1MB, 0)
            Write-Progress -Activity "Downloading $($d.file)" -Status "$mb MB" -PercentComplete $pct
        } | Out-Null

        $wc.DownloadFile($d.url, $outPath)
        Write-Host "  [DONE] $($d.file)" -ForegroundColor Green
    }
    catch {
        Write-Host "  [FAIL] $($d.file): $_" -ForegroundColor Red
        # Try fallback via curl
        Write-Host "  Retrying with curl..." -ForegroundColor Yellow
        & curl.exe -L --retry 5 --retry-delay 3 -o $outPath $d.url
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [DONE via curl] $($d.file)" -ForegroundColor Green
        }
    }
}

Write-Host "`nAll downloads complete. Files in: $dest`n" -ForegroundColor Cyan
Get-ChildItem $dest -Filter "*.gguf" | Select-Object Name, @{N="MB";E={[math]::Round($_.Length/1MB,0)}}
