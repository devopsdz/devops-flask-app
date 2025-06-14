Write-Host "🔎 Getting failed GitHub Actions runs..."

# جلب كل الـ runs بصيغة JSON
$allRuns = gh run list --limit 1000 --json databaseId,conclusion | ConvertFrom-Json

if (-not $allRuns) {
    Write-Host "❌ No runs found or failed to fetch data."
    exit
}

# تصفية الـ failed فقط
$failedRuns = $allRuns | Where-Object { $_.conclusion -eq "failure" }

if (-not $failedRuns) {
    Write-Host "✅ No failed runs found."
    exit
}

Write-Host "🗑️ Deleting $($failedRuns.Count) failed runs..."

# حذف كل run
foreach ($run in $failedRuns) {
    $runId = $run.databaseId
    if ($runId) {
        Write-Host "➡️ Deleting run ID: $runId"
        echo Y | gh run delete $runId
    } else {
        Write-Host "⚠️ Skipping: databaseId missing."
    }
}

Write-Host "✅ All failed runs deleted."

