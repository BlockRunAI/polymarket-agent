# Contributing to Polymarket AI Agent

Thank you for your interest in contributing! This project is about pushing the boundaries of AI reasoning in prediction markets. Every contribution helps us understand what AI agents can (and can't) do with real economic decisions.

## 🎯 High-Priority Features

See the [Roadmap](README.md#roadmap) for detailed feature proposals. We're especially interested in:

1. **Model Debate System** - Make models challenge each other's reasoning
2. **News Sentiment Integration** - Add real-time news context via GDELT or similar
3. **Temporal Reasoning Checks** - Prevent time-confusion errors
4. **Historical Fact Verification** - Reduce hallucinations about historical data
5. **Whale Tracker Agent** - Monitor smart money movements

## 🚀 Getting Started

### 1. Fork and Clone

```bash
git clone https://github.com/YourUsername/polymarket-agent.git
cd polymarket-agent
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.template .env
```

### 3. Configure for Development

Edit `.env` with your credentials:
- **BLOCKRUN_WALLET_KEY** - For AI payments (get testnet USDC on Base Sepolia)
- **POLYGON_WALLET_PRIVATE_KEY** - For trading (use testnet if available)
- **USE_GCS_STORAGE=false** - Use local storage for development

### 4. Run Locally

```bash
python app.py
# Visit http://127.0.0.1:5000
```

## 🏗️ Project Architecture

```
polymarket-agent/
├── src/
│   ├── agent.py              # Main orchestrator
│   ├── market/
│   │   └── polymarket.py     # Market data fetching
│   ├── analysis/
│   │   └── ai_analyzer.py    # Multi-model consensus
│   ├── trading/
│   │   ├── executor.py       # Order execution
│   │   └── wallet.py         # Wallet management
│   ├── signals/              # Trading signals (whale tracking, etc.)
│   └── storage/
│       └── gcs_storage.py    # Persistent storage
├── templates/                # Web UI
├── app.py                    # Flask application
└── main.py                   # CLI entry point
```

## 📝 Code Style

- **Python:** Follow PEP 8
- **Line length:** 100 characters max
- **Docstrings:** Use for all public functions
- **Type hints:** Encouraged but not required
- **Logging:** Use `logger.info()` for important events, `logger.debug()` for details

**Example:**
```python
def analyze_market(question: str, current_odds: float) -> Dict[str, Any]:
    """
    Analyze a prediction market using multi-model consensus.

    Args:
        question: Market question (e.g., "Will Bitcoin reach $150K?")
        current_odds: Current YES probability (0.0 to 1.0)

    Returns:
        Dictionary with consensus, probability, and reasoning
    """
    logger.info(f"Analyzing: {question}")
    # Implementation...
```

## 🧪 Testing

Before submitting a PR:

```bash
# Run the agent in dry-run mode (no actual trades)
python main.py --analyze

# Check that the dashboard loads
python app.py
# Visit http://127.0.0.1:5000
```

We don't have formal tests yet - **contributing a test suite would be valuable!**

## 🔄 Pull Request Process

### 1. Create a Feature Branch

```bash
git checkout -b feature/model-debate-system
```

### 2. Make Your Changes

- Keep commits focused and atomic
- Write descriptive commit messages
- Add comments for complex logic
- Update README.md if adding new features

### 3. Test Your Changes

- Run the agent locally
- Verify it doesn't break existing functionality
- Test with `USE_GCS_STORAGE=false` and `USE_GCS_STORAGE=true`

### 4. Submit PR

```bash
git push origin feature/model-debate-system
```

Then open a PR on GitHub with:
- **Clear title:** e.g., "Add model debate system for improved reasoning"
- **Description:** What problem does this solve? How does it work?
- **Testing:** How did you test it?
- **Screenshots:** If UI changes, include before/after

### 5. Code Review

We'll review your PR and may suggest changes. This is a collaborative process - don't be discouraged by feedback!

## 💡 Feature Implementation Guide

### Adding a New Analysis Feature

If you're adding a new type of analysis (news, whale tracking, etc.):

1. **Create a new module** in `src/signals/` or `src/analysis/`
2. **Follow the pattern** of existing analyzers
3. **Add configuration** to `.env.template`
4. **Document** in README.md

**Example structure:**
```python
# src/signals/news_analyzer.py
import logging

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    def __init__(self, api_key: str = None):
        """Initialize news analyzer with optional API credentials"""
        self.api_key = api_key
        logger.info("News analyzer initialized")

    def get_sentiment(self, question: str) -> Dict[str, Any]:
        """
        Fetch news sentiment for a market question.

        Args:
            question: Market question

        Returns:
            Dictionary with sentiment score and articles
        """
        # Implementation...
        return {
            "sentiment": 0.7,  # -1 to 1
            "articles": [...],
            "summary": "Recent news is bullish"
        }
```

### Integrating with Existing Consensus

To add your feature to the decision-making process:

```python
# In src/agent.py or app.py
from src.signals.news_analyzer import NewsAnalyzer

# Initialize
news_analyzer = NewsAnalyzer(api_key=os.getenv("NEWS_API_KEY"))

# Use in analysis
news_sentiment = news_analyzer.get_sentiment(question)

# Pass to AI models
analysis = analyzer.consensus_analysis(
    question=question,
    current_odds=yes_odds,
    news_context=news_sentiment  # NEW
)
```

## 🐛 Reporting Issues

Found a bug? Have a feature idea? Open an issue!

**For bugs:**
- Describe what happened vs. what you expected
- Include error messages and logs
- Provide steps to reproduce
- Mention your Python version and OS

**For features:**
- Explain the problem it solves
- Describe your proposed solution
- Link to relevant research or examples

## 🤔 Questions?

- **GitHub Issues** - For bugs and feature requests
- **GitHub Discussions** - For questions and ideas
- **Twitter** - [@BlockRunAI](https://x.com/BlockRunAI)

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Acknowledgments

This project builds on learnings from the broader prediction market AI community, including:
- [@ahall_research](https://x.com/ahall_research) - Kalshi agent insights
- [Manifold Markets](https://manifold.markets/) - Prediction market design
- [Polymarket](https://polymarket.com/) - Real-world market data

---

**Ready to contribute?** Pick a feature from the [Roadmap](README.md#roadmap) and open an issue to discuss your approach. We're excited to see what you build!
