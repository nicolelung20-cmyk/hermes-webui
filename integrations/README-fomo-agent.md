# ANNE FOMO read-only research agent

This integration uses the independent FOMO API at https://fomoapi.io/docs. It is a research/reporting workflow only.

## What it does

- Reads the 24-hour trader leaderboard (top 10).
- Reads the trending-token board (top 10).
- Produces a Markdown report with reported PnL, trading volume, token momentum, and API credit usage.
- Never places trades, buys tokens, signs wallet messages, or upgrades a plan.

Two bounded API reads per run are expected to cost about 500 credits when metered. The provider documents a free tier of 250,000 credits/month; actual usage is reported by the API response headers. Treat third-party metrics as reported data, not verified returns or investment advice.

## Enable the scheduled agent

1. Create a free API key at https://fomoapi.io/ (no paid plan is needed for this workflow).
2. In the GitHub repository settings, open **Secrets and variables → Actions** and add a repository secret named `FOMO_API_KEY`. Paste the key into GitHub's secret field only; do not commit it or put it in chat, issue comments, logs, or files.
3. After this branch is reviewed and merged, open **Actions → FOMO Read-Only Research Brief → Run workflow** to test a manual run. The workflow also runs daily at 13:00 UTC.
4. Open the successful run and download the `fomo-research-brief` artifact. Artifacts are retained for 14 days.

## Local run

Set `FOMO_API_KEY` in your shell environment or secure secret manager, then run:

```sh
python3 integrations/fomo_readonly_agent.py
```

Do not place the key directly in shell history or command-line arguments. On a Mac, use Keychain or another secure secret manager and export the variable only in the process environment.

## Limits and safety

- No auto-trading, wallet connection, signing, token purchase, deployment, or paid API upgrade.
- HTTP 401 means the secret is missing or invalid; HTTP 402 means credits are exhausted. The script stops rather than upgrading or paying.
- The free plan has usage limits and the provider may delay its app-feed stream after the first seven days. This workflow uses REST snapshots, not a streaming bot.
- This branch is a draft integration. It has not been run against a real API key or verified in GitHub Actions yet.
