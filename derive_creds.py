#!/usr/bin/env python3
"""
Derive Polymarket API credentials from your wallet.
Run this ONCE locally to get credentials, then add them to your .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()

def main():
    pk = os.getenv('POLYGON_WALLET_PRIVATE_KEY', '')
    if not pk:
        print("ERROR: No POLYGON_WALLET_PRIVATE_KEY in .env")
        return

    if not pk.startswith('0x'):
        pk = '0x' + pk

    try:
        from py_clob_client.client import ClobClient

        print("Connecting to Polymarket CLOB...")
        client = ClobClient(
            host='https://clob.polymarket.com',
            chain_id=137,
            key=pk
        )

        print("Deriving API credentials...")
        creds = client.create_or_derive_api_creds()

        # Handle both dict and object formats
        if isinstance(creds, dict):
            api_key = creds.get("apiKey")
            api_secret = creds.get("secret")
            passphrase = creds.get("passphrase")
        else:
            api_key = getattr(creds, "api_key", None)
            api_secret = getattr(creds, "api_secret", None)
            passphrase = getattr(creds, "api_passphrase", None)

        print("\n" + "=" * 60)
        print("SUCCESS! Add these to your .env file:")
        print("=" * 60)
        print(f"POLYMARKET_API_KEY={api_key}")
        print(f"POLYMARKET_API_SECRET={api_secret}")
        print(f"POLYMARKET_PASSPHRASE={passphrase}")
        print("=" * 60)

    except ImportError:
        print("ERROR: py-clob-client not installed. Run: pip install py-clob-client")
    except Exception as e:
        print(f"ERROR: {e}")
        print("\nMake sure your wallet is registered at polymarket.com first!")

if __name__ == "__main__":
    main()
