name: Daily AI Report Update

on:
  schedule:
    - cron: '30 7 * * 1-5'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install yfinance pandas numpy google-generativeai

      - name: Run AI Database Builder
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python update_db.py

      - name: Commit and Push
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add ai_database.json
          git commit -m "Auto-update AI report" || exit 0
          git push
