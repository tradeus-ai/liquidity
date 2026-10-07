# Trading Alert System Design Document

## 1. Overview
An automated trading alert system written in Python that monitors financial instruments (from `Futures.csv`), applies SMC (Smart Money Concepts) rules derived from Pine Script, and sends trade alerts to a Telegram channel. The system operates on Higher Timeframes (Daily) for trend/zones and Lower Timeframes (15m/1h) for entries. It will be deployed to Oracle Cloud Infrastructure (OCI) using Terraform.

## 2. Architecture
- **Data Ingestion**: A Python script running in a continuous loop fetching OHLCV data using a TradingView data fetching library (e.g., `tvDatafeed`). It processes all symbols concurrently using `asyncio` or `ThreadPoolExecutor`.
- **Core Engine (Python)**:
  - Structured modularly into `data_fetcher.py`, `strategy_engine.py`, `alert_manager.py`, and `main.py`.
  - Uses the PyPI `smartmoneyconcepts` library to significantly reduce manual translation of complex logic for pullbacks, swing highs/lows, BOS, and ChoCH.
  - Custom overrides where necessary to exactly match `liquidity_sweep.pine` and `order_blocks.pine`.
- **Alerting Service**: Integrates with Telegram Bot API to broadcast signals. Uses an SQLite-backed retry queue with exponential backoff to handle network failures gracefully.
- **Infrastructure**: Terraform config for an OCI Compute Instance. We will reuse the existing Terraform setup in `infrastructure/` to deploy the Ubuntu VM and inject SSH keys.

## 3. Trading Strategy Rules
### Entries:
**Condition 1 (Confluence)**:
- 1a. Liquidity Sweep occurs.
- 1b. Price reacts from an Order Block.
- 1c. Price reacts from an FVG (excluding inside bar zones).

**Condition 2 (Execution trigger)**:
- **Buy Entry**: The entry candle must close inside a recent Bearish FVG.
  - **Stop Loss**: Recent swing low (SMC pullback).
  - **Targets**: Next 2 swing highs (SMC pullback).
- **Sell Entry**: The entry candle must close inside a recent Bullish FVG.
  - **Stop Loss**: Recent swing high (SMC pullback).
  - **Targets**: Next 2 swing lows (SMC pullback).

### Timeframes:
- **HTF**: Daily (Trend, Supply/Demand Zones).
- **LTF**: 15m (Indian Markets) / 1h (Forex) for entry triggers.

## 4. OCI Infrastructure & Deployment (Terraform)
- **OCI Provider**: Configure OCI credentials.
- **Compute Instance**: Provision an Oracle Linux or Ubuntu VM. Reusing the existing `infrastructure/main.tf` logic.
- **Networking**: VCN, Subnet, Security List (Outbound internet for Telegram and TV data).

## 5. Development Phases
1. **Python Strategy Engine**: Integrate `smartmoneyconcepts` and map to Pine Script logic.
2. **Data Integration**: Connect to TV data source with concurrent fetch setup.
3. **Telegram Integration**: Set up bot and resilient SQLite retry queue.
4. **Deployment**: Deploy to the OCI instance via SSH/Git pull using the existing Terraform.

## 6. NOT in scope
- A full CI/CD pipeline (e.g., GitHub actions). Code deployment will rely on the existing manual SSH/git-pull approach used in the `infrastructure/` directory.
- Translating the entire SMC suite from scratch line-by-line; relying on `smartmoneyconcepts` as the foundational layer.

## 7. What already exists
- Terraform infrastructure scripts in `infrastructure/` directory.
- Custom Pine Script indicators (`liquidity_sweep.pine`, `order_blocks.pine`, `tradeus_liquidity_toolkit.pine`).
- PyPI `smartmoneyconcepts` library for the heavy lifting of SMC logic.

## Implementation Tasks
Synthesized from this review's findings. Each task derives from a specific finding above. Run with Claude Code or Codex; checkbox as you ship.

- [ ] **T1 (P1, human: ~1h / CC: ~10min)** — Infrastructure — Re-use existing Terraform setup for deployment
  - Surfaced by: Architecture: CI/CD Pipeline - User requested to use existing OCI setup in infrastructure/
  - Files: `infrastructure/main.tf`
- [ ] **T2 (P1, human: ~30min / CC: ~5min)** — Core — Scaffold modular Python architecture
  - Surfaced by: Code Quality: Module Structure - Decided to split code into 4 main modules
  - Files: `data_fetcher.py`, `strategy_engine.py`, `alert_manager.py`, `main.py`
- [ ] **T3 (P1, human: ~4h / CC: ~30min)** — Strategy — Implement concurrent data fetch and SMC engine
  - Surfaced by: Scope: Translation Complexity & Performance - Use smartmoneyconcepts and asyncio/ThreadPool
  - Files: `data_fetcher.py`, `strategy_engine.py`, `requirements.txt`
- [ ] **T4 (P1, human: ~1h / CC: ~10min)** — Alerts — Implement SQLite-backed Telegram alert retry system
  - Surfaced by: Architecture: Alert Delivery Guarantees - Retry mechanism with exponential backoff and SQLite
  - Files: `alert_manager.py`

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | — |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | — | — |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | clean | 4 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | — |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | — |

VERDICT: CLEARED — Eng Review passed
NO UNRESOLVED DECISIONS
