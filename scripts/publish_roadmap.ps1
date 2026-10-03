[CmdletBinding()]
param([switch]$Publish, [switch]$Verify)
# Dry-run by default. Credentials stay in memory and never enter the manifest.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$planPath = Join-Path $repoRoot 'docs/roadmap/plan.json'
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
if ($plan.owner -ne 'Protagonist01' -or $plan.repo -ne 'url-shortener') {
    throw 'This publisher is scoped to owner-confirmed Protagonist01/url-shortener.'
}
$seen = @{}
foreach ($issue in $plan.issues) {
    if ($seen.ContainsKey($issue.key)) { throw "Duplicate key: $($issue.key)" }
    foreach ($dep in $issue.dependencies) {
        if (-not $seen.ContainsKey($dep)) { throw "Missing or unordered dependency: $dep" }
    }
    if (-not ($plan.milestones | Where-Object key -eq $issue.stage)) { throw "Missing milestone: $($issue.stage)" }
    $seen[$issue.key] = $true
}
if (-not $Publish -and -not $Verify) {
    Write-Output "Valid plan: $($plan.milestones.Count) milestones, $($plan.issues.Count) issues. No GitHub writes performed."
    return
}
$credentialInput = 'protocol=https' + [char]10 + 'host=github.com' + [char]10 + [char]10
$credentialOutput = $credentialInput | git -c credential.interactive=never credential fill 2>$null
$passwordLine = @($credentialOutput | Where-Object { $_ -like 'password=*' } | Select-Object -First 1)
if ($passwordLine.Count -ne 1) { throw 'No existing GitHub Git credential is available.' }
$credentialPassword = $passwordLine[0].Substring(9)
$headers = @{
    Authorization = "Bearer $credentialPassword"
    Accept = 'application/vnd.github+json'
    'X-GitHub-Api-Version' = '2026-03-10'
    'User-Agent' = 'QR-Roadmap-Setup'
}
$apiRoot = "https://api.github.com/repos/$($plan.owner)/$($plan.repo)"
function Read-Paged([string]$Path) {
    $items = @()
    for ($pageIndex = 1; ; $pageIndex++) {
        $separator = if ($Path.Contains('?')) { '&' } else { '?' }
        $pageUrl = $apiRoot + '/' + $Path + $separator + "per_page=100&page=$pageIndex"
        $pageResponse = Invoke-RestMethod -Uri $pageUrl -Headers $headers
        $pageItems = @($pageResponse)
        $items += $pageItems
        if ($pageItems.Count -lt 100) { return $items }
    }
}
function Write-Api([string]$Path, [hashtable]$Body) {
    $json = $Body | ConvertTo-Json -Depth 15
    # Never retry POST automatically: a timeout may occur after a successful write.
    Invoke-RestMethod -Method Post -Uri "$apiRoot/$Path" -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($json))
}
function Save-Plan {
    $text = $plan | ConvertTo-Json -Depth 25
    [IO.File]::WriteAllText($planPath, $text + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}
try {
    $identity = Invoke-RestMethod -Uri 'https://api.github.com/user' -Headers $headers
    if ($identity.login -ne $plan.owner) { throw 'Credential account does not match the confirmed owner.' }
    $repo = Invoke-RestMethod -Uri $apiRoot -Headers $headers
    if ($Publish -and -not $repo.permissions.push) { throw 'Repository write access unavailable.' }
    $milestones = @(Read-Paged 'milestones?state=all')
    $issues = @(Read-Paged 'issues?state=all' | Where-Object { -not $_.pull_request })
    if ($Publish) {
        foreach ($stage in $plan.milestones) {
            $matches = @($milestones | Where-Object title -eq $stage.title)
            if ($matches.Count -gt 1) { throw "Duplicate milestone: $($stage.title)" }
            if ($matches.Count -eq 0) {
                $item = Write-Api 'milestones' @{
                    title = $stage.title
                    state = 'open'
                    description = "$($stage.gate) Exit gate: all issues verified; relevant security/accessibility/performance/recovery evidence recorded. Roadmap: docs/ROADMAP.md. No due date without an owner-approved schedule."
                }
                $milestones += $item
            } else { $item = $matches[0] }
            $stage.number = $item.number
            $stage.url = $item.html_url
            Save-Plan
        }
        foreach ($task in $plan.issues) {
            $marker = "<!-- qr-roadmap:$($task.key) -->"
            $matches = @($issues | Where-Object { $_.title -eq $task.title -or ($_.body -and $_.body.Contains($marker)) })
            if ($matches.Count -gt 1) { throw "Duplicate roadmap issue: $($task.key); review before continuing." }
            $stage = $plan.milestones | Where-Object key -eq $task.stage
            if ($matches.Count -eq 0) {
                $dependencyLines = @()
                foreach ($depKey in $task.dependencies) {
                    $dependency = $plan.issues | Where-Object key -eq $depKey
                    if (-not $dependency.number) { throw "Unpublished prerequisite: $depKey" }
                    $dependencyLines += ('- {0}: {1}' -f $depKey, $dependency.url)
                }
                if ($dependencyLines.Count -eq 0) { $dependencyLines = @('- No prerequisite issue. Clarify required decisions before dependent implementation.') }
                $body = $task.body_template.Replace('{{dependencies}}', ($dependencyLines -join [Environment]::NewLine))
                $item = Write-Api 'issues' @{ title = $task.title; body = $body; milestone = $stage.number }
                $issues += $item
            } else {
                $item = $matches[0]
                if ($item.milestone.number -ne $stage.number) { throw "Different milestone on existing issue: $($task.key)" }
                # Preserve existing issue bodies/state; never reset user edits on rerun.
            }
            $task.number = $item.number
            $task.url = $item.html_url
            Save-Plan
            Write-Output "$($task.key) -> #$($item.number)"
        }
        $plan.publication.state = 'published'
        $plan.publication.notes = 'Milestones and issues published through GitHub REST using the existing Git credential helper. MCP reads succeeded; MCP issue creation returned an unsubmitted interactive form.'
        Save-Plan
    }
    if ($Verify) {
        $milestones = @(Read-Paged 'milestones?state=all')
        $issues = @(Read-Paged 'issues?state=all' | Where-Object { -not $_.pull_request })
        foreach ($stage in $plan.milestones) {
            $matching = @($milestones | Where-Object title -eq $stage.title)
            if ($matching.Count -ne 1 -or $matching[0].number -ne $stage.number) { throw "Milestone verification failed: $($stage.key)" }
        }
        foreach ($task in $plan.issues) {
            $marker = "<!-- qr-roadmap:$($task.key) -->"
            $matching = @($issues | Where-Object { $_.title -eq $task.title -or ($_.body -and $_.body.Contains($marker)) })
            $stage = $plan.milestones | Where-Object key -eq $task.stage
            if ($matching.Count -ne 1 -or $matching[0].number -ne $task.number -or $matching[0].milestone.number -ne $stage.number) {
                throw "Issue identity/milestone verification failed: $($task.key)"
            }
            foreach ($depKey in $task.dependencies) {
                $dependency = $plan.issues | Where-Object key -eq $depKey
                if (-not $matching[0].body.Contains($dependency.url)) { throw "Missing dependency link: $($task.key) -> $depKey" }
            }
        }
        Write-Output "Verified $($plan.milestones.Count) milestones and $($plan.issues.Count) unique issues, milestone assignments and dependency links."
    }
} finally {
    Remove-Variable credentialInput,credentialOutput,passwordLine,credentialPassword,headers -ErrorAction SilentlyContinue
}
