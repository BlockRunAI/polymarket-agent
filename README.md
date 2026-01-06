# Polymarket AI Agent by BlockRunAI

<div align="center">

![Polymarket AI Agent](https://img.shields.io/badge/Polymarket-AI%20Agent-00f0ff?style=for-the-badge&logo=ethereum&logoColor=white)
![x402 Protocol](https://img.shields.io/badge/x402-Protocol-00ff88?style=for-the-badge)
![BlockRun](https://img.shields.io/badge/BlockRun-AI-a855f7?style=for-the-badge)

**An autonomous AI-powered prediction market trading agent**

*Built for the [x402 Hackathon](https://x402.org) by [BlockRunAI](https://blockrun.ai)*

[Live Demo](https://polymarket-agent-516729397241.europe-west1.run.app) | [Documentation](#quick-start) | [BlockRun](https://blockrun.ai)

</div>

---

## The Vision: Truly Autonomous AI Agents

**What if AI agents could be real economic actors?**

Today's AI agents are puppets - they need developers to manage API keys, monitor credits, and handle payments. They can't make real economic decisions because they don't control real money.

**This project changes that.**

With the x402 protocol and BlockRun, this Polymarket agent is a **real economic entity**:

- **Has its own wallet** - Not managed by a developer, owned by the agent
- **Pays for its own AI** - No API keys, just USDC micropayments
- **Makes trading decisions** - Analyzes markets, sizes positions, executes trades
- **Manages its own budget** - Decides when expensive analysis is worth it

> **This is what autonomous means.** An agent that earns money from prediction markets and spends money on AI services - all without human intervention.

---

## Why We Built This

We believe the future of AI is **agentic** - AI systems that can act independently in the real world. But true autonomy requires economic autonomy.

Traditional approaches fail because:
- API keys = developer dependency
- Prepaid credits = budget controlled by humans
- Single provider = no choice, no optimization

The x402 protocol solves this by making payments as simple as HTTP requests. BlockRun brings this to AI - 600+ models, pay-per-request, no keys needed.

**This agent is our proof that autonomous AI economies are possible today.**

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-Model AI Consensus** | GPT-4o, Claude, Gemini vote on predictions |
| **Live Market Data** | Real-time data from Polymarket Gamma API |
| **Kelly Criterion Sizing** | Mathematical optimal position sizing |
| **Autonomous Payments** | Agent pays for its own AI via x402 |
| **Web Dashboard** | Beautiful dark-themed monitoring UI |
| **Trade Execution** | Direct order placement on Polygon |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    POLYMARKET AI AGENT                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   Market    │    │     AI      │    │   Trading   │         │
│  │    Data     │───▶│  Analysis   │───▶│  Execution  │         │
│  │  (Gamma)    │    │ (BlockRun)  │    │  (Polygon)  │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                            │                                    │
│                            ▼                                    │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              AGENT WALLET (Dual Chain)               │       │
│  │                                                      │       │
│  │   Base Chain          │        Polygon Chain         │       │
│  │   (AI Payments)       │        (Trading)             │       │
│  │   USDC ───────────────┼──────────▶ USDC             │       │
│  │                       │                              │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     x402 PROTOCOL LAYER                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Agent Request ──▶ 402 Payment Required ──▶ Sign USDC          │
│                                               ──▶ AI Response   │
│                                                                 │
│  No API keys. No prepayment. Pay only for what you use.        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/BlockRunAI/polymarket-agent.git
cd polymarket-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Polymarket Account Setup

**IMPORTANT:** Polymarket uses a **proxy wallet system**. Understanding this is critical for successful trading.

#### How Polymarket Wallets Work

When you sign into Polymarket, a **Gnosis Safe proxy wallet** is automatically deployed for you. This means you have TWO addresses:

| Address Type | Purpose | Example |
|--------------|---------|---------|
| **Signer (EOA)** | Your private key wallet - signs transactions | `0x4069...3A7` |
| **Proxy (Gnosis Safe)** | Holds your funds on Polymarket | `0x84f8...d2b` |

**Why two addresses?**
- Your private key signs orders
- Your proxy wallet holds USDC and executes trades
- This enables "gasless" trading through relayers

#### Step-by-Step Setup

**Step 1: Get Your Proxy Wallet Address**

1. Go to https://polymarket.com
2. Connect with your wallet (MetaMask, WalletConnect, etc.)
3. Sign in and accept terms of service
4. Go to **Settings** → **Wallet**
5. Copy the address shown - **this is your PROXY wallet** (not your signer wallet!)

**Step 2: Get Your Private Key**

Export your wallet's private key:
- **MetaMask:** Account Details → Export Private Key
- **Other wallets:** Follow wallet-specific export instructions

⚠️ **Security:** Never share your private key. It should only be in your `.env` file.

**Step 3: Choose API Credential Strategy**

You have two options:

**Option A: Auto-Derive Credentials (Easier)**
- Agent will derive credentials automatically on first run
- No manual setup needed
- Credentials will be logged for you to save

**Option B: Pre-Generate Credentials (Recommended for Production)**
- More reliable for repeated deployments
- Avoids derivation issues
- See "Generating API Credentials" below

#### Generating API Credentials (Optional but Recommended)

Run this Python script to generate credentials:

```python
from py_clob_client.client import ClobClient

# Your setup
PRIVATE_KEY = "0x..."  # Your signer private key
PROXY_WALLET = "0x..."  # From Polymarket settings

client = ClobClient(
    "https://clob.polymarket.com",
    key=PRIVATE_KEY,
    chain_id=137,
    signature_type=2,  # Gnosis Safe proxy
    funder=PROXY_WALLET
)

creds = client.create_or_derive_api_creds()
print(f"POLYMARKET_API_KEY={creds['apiKey']}")
print(f"POLYMARKET_API_SECRET={creds['secret']}")
print(f"POLYMARKET_PASSPHRASE={creds['passphrase']}")
```

Save these to your `.env` file.

#### Understanding Signature Types

| Type | Value | Use Case | Your Setup |
|------|-------|----------|------------|
| EOA | `0` | Direct wallet (signer = funder) | If NOT using proxy |
| POLY_PROXY | `1` | Magic Link email wallets | Rare |
| **GNOSIS_SAFE** | `2` | **Standard Polymarket proxy** | **Most users (YOU!)** |

The agent automatically detects your signature type based on whether signer ≠ funder.

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# BlockRun AI Payments (Base chain)
BLOCKRUN_WALLET_KEY=0x...your_private_key

# Polymarket Trading (Polygon chain)
# This is your SIGNER wallet private key (the one you exported)
POLYGON_WALLET_PRIVATE_KEY=0x...your_private_key

# Your PROXY wallet address (from Polymarket settings page)
POLYMARKET_PROXY_WALLET=0x...your_proxy_address

# Polymarket API Credentials (optional but recommended)
# If omitted, agent will try to derive them automatically
POLYMARKET_API_KEY=your_api_key
POLYMARKET_API_SECRET=your_api_secret
POLYMARKET_PASSPHRASE=your_passphrase

# Dashboard Auth
ADMIN_USER=admin
ADMIN_PASS=your_secure_password

# Trading Parameters
INITIAL_BANKROLL=100
MAX_BET_PERCENTAGE=0.05
```

> **Pro Tip:** You can use the same private key for both Base and Polygon - same address works on both chains!

### 4. Fund Your Wallets

| Chain | Token | Purpose | Suggested |
|-------|-------|---------|-----------|
| Base | USDC | AI payments | $10-20 |
| Polygon | USDC.e | Trading | $50-100 |

**CRITICAL:** Fund your **PROXY wallet** (from Step 2), not your signer wallet!
- On Polymarket, deposit USDC to the address shown in Settings
- The proxy wallet is where trades execute from

### 5. Run

```bash
# Start web dashboard
python app.py

# Visit http://127.0.0.1:5000
```

Or use the CLI:

```bash
# Check status
python main.py --status

# Analyze markets
python main.py --analyze

# Run with live trading
python main.py --live
```

---

## How It Works

### 1. Fetch Markets (Free)
```python
from src.market import fetch_active_markets
markets = fetch_active_markets(limit=20)
```

### 2. AI Consensus Analysis (Pay-per-request)
```python
from src.analysis import get_analyzer
analyzer = get_analyzer()

# 3 models vote: GPT + Gemini + Claude
result = analyzer.consensus_analysis(
    question="Will Bitcoin reach $150K by June 2025?",
    current_odds=0.35
)
# Returns: consensus, avg_probability, recommendation
```

### 3. Position Sizing (Kelly Criterion)
```python
# Optimal bet size based on edge and confidence
bet_size = executor.calculate_position_size(
    edge=0.15,      # 15% expected edge
    confidence=7,   # AI confidence (1-10)
    bankroll=100
)
```

### 4. Execute Trade (Polygon)
```python
result = executor.execute_signal(
    token_id="0x...",
    action="BET YES",
    edge=0.15,
    confidence=7,
    consensus="BULLISH"
)
```

---

## x402 Protocol Integration

The agent uses [BlockRun](https://blockrun.ai) to access AI services via the x402 protocol:

1. Agent makes request to BlockRun
2. BlockRun returns `402 Payment Required`
3. Agent signs USDC transfer (EIP-3009)
4. BlockRun processes request and returns response
5. USDC is transferred atomically

**No API keys. No prepayment. True pay-per-use.**

### Available Models

| Model | Use Case | ~Cost/request |
|-------|----------|---------------|
| `openai/gpt-4o-mini` | Fast screening | $0.001 |
| `google/gemini-2.5-flash` | Quick analysis | $0.001 |
| `anthropic/claude-haiku-4.5` | Reasoning | $0.001 |
| `anthropic/claude-sonnet-4` | Deep analysis | $0.003 |
| `anthropic/claude-opus-4` | Complex tasks | $0.015 |

---

## Multi-Agent Architecture

Our agent uses a **swarm architecture** with specialized agents for different tasks:

| Agent | Status | Description |
|-------|--------|-------------|
| **Market Analysis Agent** | Active | 3-model consensus for predictions |
| **News Agent** | Coming Soon | Real-time news sentiment analysis |
| **Edge Detection Agent** | Coming Soon | Arbitrage & inefficiency detection |
| **Whale Tracker Agent** | Coming Soon | Smart money movement tracking |

The vision: agents that can **call other agents** via x402, creating an autonomous economy of specialized AI services.

---

## LLM Evaluation System

We use a **3-model consensus** system for robust predictions:

```
┌─────────────────────────────────────────────────────────┐
│              3-MODEL CONSENSUS SYSTEM                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   GPT-4o-mini     Gemini Flash     Claude Haiku        │
│   (OpenAI)        (Google)         (Anthropic)         │
│       │               │                │               │
│       ▼               ▼                ▼               │
│   ┌───────┐       ┌───────┐       ┌───────┐           │
│   │ YES   │       │ YES   │       │  NO   │           │
│   │ 65%   │       │ 70%   │       │ 45%   │           │
│   └───────┘       └───────┘       └───────┘           │
│       │               │                │               │
│       └───────────────┼────────────────┘               │
│                       ▼                                 │
│              ┌─────────────────┐                       │
│              │ CONSENSUS: YES  │                       │
│              │ (2/3 agree)     │                       │
│              └─────────────────┘                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Why multiple models?**
- Reduces single-model bias
- Different training data = different perspectives
- Only trade when 2+ models agree (higher confidence)

---

## Roadmap

| Status | Feature | Description |
|--------|---------|-------------|
| ✅ | Multi-Model Consensus | 3 LLMs vote on each prediction |
| ✅ | Autonomous Payments | Agent pays for AI via x402 |
| 🔄 | Agent Orchestration | Multiple specialized agents |
| 🔮 | Agents Calling Agents | Agents pay other agents via x402 |
| 🔮 | Agent Marketplace | Discover and hire specialized agents |
| 🔮 | Autonomous Economy | Self-sustaining agent ecosystems |

---

## Project Structure

```
polymarket-agent/
├── app.py                    # Flask web dashboard
├── main.py                   # CLI entry point
├── requirements.txt
│
├── src/
│   ├── agent.py              # Main orchestrator
│   ├── market/
│   │   └── polymarket.py     # Gamma API client
│   ├── analysis/
│   │   └── ai_analyzer.py    # BlockRun AI integration
│   └── trading/
│       ├── wallet.py         # Wallet management
│       └── executor.py       # Trade execution
│
└── templates/
    ├── index.html            # Dashboard UI
    └── setup.html            # Setup guide
```

---

## Deployment Requirements

### Geographic Restrictions (Important!)

Polymarket's CLOB API enforces geographic restrictions via Cloudflare. **Order placement (`POST /order`) will fail with `403 Forbidden`** if deployed to blocked regions.

| Region | Status | Notes |
|--------|--------|-------|
| **United States** | Blocked | CFTC settlement (2022) |
| **European Union** | Blocked | Belgium, France, Poland specifically |
| **United Kingdom** | Blocked | No UKGC approval |
| **Singapore** | Blocked | Remote gambling laws |
| **Australia** | Blocked | Remote gambling laws |
| **Japan (Tokyo)** | Allowed | Recommended deployment region |
| **Taiwan** | Allowed | Alternative option |

**Note:** `GET` requests (market data, orderbook) work from any region. Only `POST` requests (order placement) are blocked.

### Recommended Deployment

Deploy to **Tokyo (`asia-northeast1`)** for reliable order execution:

```bash
./deploy-tokyo.sh
```

---

## Troubleshooting

### Common Errors and Solutions

#### ❌ Error: `PolyApiException: invalid signature` (400)

**Cause:** Incorrect signature type for your wallet setup.

**Solution:**
1. Verify you're using a proxy wallet: Check if `POLYMARKET_PROXY_WALLET` is set and different from your signer address
2. The agent should auto-detect `signature_type=2` (Gnosis Safe) when proxy ≠ signer
3. If still failing, your API credentials may be wrong - delete them from `.env` and let the agent re-derive them

**Check your setup:**
```python
# Your addresses should be DIFFERENT:
Signer:  0x4069...  (POLYGON_WALLET_PRIVATE_KEY)
Proxy:   0x84f8...  (POLYMARKET_PROXY_WALLET)
```

#### ❌ Error: `403 Forbidden` on order placement

**Cause:** Deployed to a geoblocked region.

**Solution:** Deploy to Tokyo (`asia-northeast1`) instead:
```bash
./deploy-tokyo.sh
```

See [Deployment Requirements](#deployment-requirements) for allowed regions.

#### ❌ Error: No markets found / Markets filtered out

**Cause:** Markets have extreme odds (99/1) or low liquidity.

**Solution:** The agent filters for tradeable markets (15%-85% odds, $5K+ liquidity). This is intentional to avoid markets with no edge potential. If you want different thresholds, edit `src/market/polymarket.py`:

```python
markets = fetch_active_markets(
    limit=50,
    min_odds=0.10,      # Adjust minimum (default 0.15)
    max_odds=0.90,      # Adjust maximum (default 0.85)
    min_liquidity=1000  # Adjust min liquidity (default 5000)
)
```

#### ❌ Error: Could not derive API credentials

**Cause:** Wallet not registered with Polymarket.

**Solution:**
1. Go to https://polymarket.com
2. Connect with the wallet for `POLYGON_WALLET_PRIVATE_KEY`
3. Sign in and accept terms of service
4. Wait for proxy wallet to deploy (~1 minute)
5. Get your proxy address from Settings → Wallet
6. Retry agent initialization

#### ❌ Dashboard shows "Agent not configured"

**Cause:** Missing or invalid environment variables.

**Solution:** Check `.env` has all required fields:
```bash
BLOCKRUN_WALLET_KEY=0x...
POLYGON_WALLET_PRIVATE_KEY=0x...
POLYMARKET_PROXY_WALLET=0x...
```

Verify wallets are funded:
- Base USDC for AI payments
- Polygon USDC in proxy wallet for trading

#### ❌ Orders fail with "insufficient balance"

**Cause:** USDC not in your proxy wallet.

**Solution:**
1. Check balance at https://polymarket.com (should show in Settings)
2. Deposit USDC to your **PROXY wallet** address (not signer!)
3. On Polymarket, the deposit address is your proxy wallet

#### ❌ Trades execute but dashboard doesn't update

**Cause:** Dashboard polling interval or caching.

**Solution:** Refresh the browser. Dashboard polls every 5 seconds - changes may take a few moments to appear.

### Getting Help

If you're still stuck:

1. **Check logs:**
   - Local: Terminal output shows detailed errors
   - Cloud Run: `gcloud run services logs read polymarket-agent --region asia-northeast1`

2. **Common issues:**
   - Private key format: Must start with `0x`
   - Proxy wallet: Must be different from signer
   - API creds: If in doubt, delete from `.env` and let agent re-derive

3. **Still broken?**
   - [Open an issue](https://github.com/BlockRunAI/polymarket-agent/issues)
   - Include error message and relevant logs (redact private keys!)

---

## Join the Movement

We're building the infrastructure for autonomous AI economies. This agent is just the beginning.

**Want to build with x402?**

- Check out [awesome-blockrun](https://github.com/BlockRunAI/awesome-blockrun) for more examples
- Join the x402 ecosystem of 1,100+ projects
- Build agents that can pay for their own compute

---

## About BlockRun.AI

[BlockRun](https://blockrun.ai) is the gateway to AI services using x402 micropayments. Access 600+ AI models with just a wallet - no API keys needed.

**Connect with us:**

| Channel | Link |
|---------|------|
| Website | [blockrun.ai](https://blockrun.ai) |
| GitHub | [@BlockRunAI](https://github.com/BlockRunAI) |
| X (Twitter) | [@BlockRunAI](https://x.com/BlockRunAI) |

**Resources:**
- [BlockRun Documentation](https://docs.blockrun.ai)
- [Python SDK](https://github.com/BlockRunAI/blockrun-llm)
- [TypeScript SDK](https://github.com/BlockRunAI/blockrun-llm-ts)
- [awesome-blockrun](https://github.com/BlockRunAI/awesome-blockrun)

---

## Disclaimer

- **Financial Risk**: Prediction market trading involves significant risk of loss
- **Jurisdiction**: Check your local laws regarding prediction markets
- **Experimental**: This is hackathon software - use at your own risk
- **Not Financial Advice**: This project is for educational purposes only

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built for the x402 Hackathon**

*Proving that autonomous AI economies are possible today*

[![BlockRun](https://img.shields.io/badge/Powered%20by-BlockRun.AI-a855f7?style=flat-square)](https://blockrun.ai)
[![x402](https://img.shields.io/badge/Protocol-x402-00ff88?style=flat-square)](https://x402.org)

</div>
