# Test all 4 cache policies
$policies = @('full_cache', 'sliding_window', 'heavy_hitter', 'bdh_inspired_state')

foreach ($policy in $policies) {
    Write-Host "`n=== Testing $policy ===" -ForegroundColor Cyan
    
    $body = @{
        policy = $policy
        n_facts = 3
        seq_len = 128
        question_target = 0
        seed = 42
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri 'http://localhost:8000/simulate' -Method POST -Body $body -ContentType 'application/json'
        
        Write-Host "✓ Status: 200 OK" -ForegroundColor Green
        Write-Host "  Policy: $($response.simulation.policy)"
        Write-Host "  Steps: $($response.simulation.steps.Count)"
        Write-Host "  Final Answer: '$($response.simulation.final_answer)'"
        Write-Host "  Ground Truth: '$($response.simulation.ground_truth)'"
        Write-Host "  Correct: $($response.simulation.correct)"
        Write-Host "  Cache Size: $($response.simulation.steps[-1].cache_size_tokens) tokens"
    }
    catch {
        Write-Host "✗ Error: $_" -ForegroundColor Red
    }
}

Write-Host "`n=== All tests completed ===" -ForegroundColor Green
