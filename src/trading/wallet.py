"""
Wallet Management Module
Handles Polygon wallet operations for Polymarket trading
"""
import os
import json
from typing import Tuple, Optional, Dict, Any
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

load_dotenv()

# Contract addresses
# USDC.e (bridged) on Polygon - used for balance display
USDC_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
POLYMARKET_EXCHANGE = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
RPC_URL = "https://polygon-rpc.com"

# USDC ABI for basic operations
USDC_ABI = json.loads('''[
    {
        "constant": true,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": true,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": false,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
]''')


class PolygonWallet:
    """Manages Polygon wallet for Polymarket trading"""

    def __init__(self, private_key: Optional[str] = None):
        """
        Initialize wallet

        Args:
            private_key: Polygon wallet private key (or from env)
        """
        self.private_key = private_key or os.getenv("POLYGON_WALLET_PRIVATE_KEY", "")

        if not self.private_key:
            raise ValueError("No private key provided")

        # Add 0x prefix if missing
        if not self.private_key.startswith("0x"):
            self.private_key = "0x" + self.private_key

        # Get signer address (EOA that signs transactions)
        self.account = Account.from_key(self.private_key)
        self.signer_address = self.account.address

        # Use proxy wallet for balance display if set, otherwise use signer
        self.address = os.getenv("POLYMARKET_PROXY_WALLET", self.signer_address)

        # Initialize Web3
        self.w3 = Web3(Web3.HTTPProvider(RPC_URL))

        if not self.w3.is_connected():
            raise ConnectionError("Failed to connect to Polygon network")

        # Initialize USDC contract
        self.usdc = self.w3.eth.contract(
            address=USDC_CONTRACT,
            abi=USDC_ABI
        )

    def get_balances(self) -> Dict[str, float]:
        """Get MATIC and USDC balances"""
        # MATIC balance
        matic_wei = self.w3.eth.get_balance(self.address)
        matic = matic_wei / 10**18

        # USDC balance
        usdc_raw = self.usdc.functions.balanceOf(self.address).call()
        usdc = usdc_raw / 10**6

        return {
            "matic": matic,
            "usdc": usdc
        }

    def get_usdc_balance(self) -> float:
        """Get USDC balance in human-readable format"""
        raw = self.usdc.functions.balanceOf(self.address).call()
        return raw / 10**6

    def get_allowance(self) -> float:
        """Get current Polymarket allowance"""
        raw = self.usdc.functions.allowance(
            self.address,
            POLYMARKET_EXCHANGE
        ).call()
        return raw / 10**6

    def check_approval(self, min_amount: float = 1.0) -> bool:
        """Check if Polymarket has sufficient USDC approval"""
        allowance = self.get_allowance()
        return allowance >= min_amount

    def approve_usdc(self, amount: Optional[float] = None) -> Optional[str]:
        """
        Approve Polymarket to spend USDC

        Args:
            amount: Amount to approve (None = unlimited)

        Returns:
            Transaction hash or None if failed
        """
        # Amount in smallest units (max if not specified)
        if amount is None:
            approve_amount = 2**256 - 1  # Max uint256
        else:
            approve_amount = int(amount * 10**6)

        try:
            # Get current gas price and add 20%
            gas_price = self.w3.eth.gas_price
            gas_price = int(gas_price * 1.2)  # 20% buffer

            # Build transaction (use signer address for transactions)
            txn = self.usdc.functions.approve(
                POLYMARKET_EXCHANGE,
                approve_amount
            ).build_transaction({
                'from': self.signer_address,
                'gas': 100000,
                'gasPrice': gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.signer_address),
            })

            # Sign and send
            signed = self.w3.eth.account.sign_transaction(txn, self.private_key)
            # Handle both old and new web3 versions
            raw_tx = getattr(signed, 'rawTransaction', None) or getattr(signed, 'raw_transaction', None)
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)

            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if receipt['status'] == 1:
                return tx_hash.hex()
            return None

        except Exception as e:
            print(f"Approval failed: {e}")
            return None

    def print_status(self) -> None:
        """Print wallet status"""
        balances = self.get_balances()
        allowance = self.get_allowance()

        print(f"Wallet: {self.address}")
        print(f"MATIC:  {balances['matic']:.4f}")
        print(f"USDC:   {balances['usdc']:.2f}")
        print(f"Polymarket Allowance: {allowance:.2f} USDC")


def get_wallet() -> Optional[PolygonWallet]:
    """Get wallet instance if configured"""
    try:
        return PolygonWallet()
    except Exception as e:
        print(f"Failed to initialize wallet: {e}")
        return None


# CLI usage
if __name__ == "__main__":
    print("=" * 60)
    print("POLYMARKET WALLET STATUS")
    print("=" * 60)

    wallet = get_wallet()
    if wallet:
        wallet.print_status()
    else:
        print("Wallet not configured. Set POLYGON_WALLET_PRIVATE_KEY in .env")
