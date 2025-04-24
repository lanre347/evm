# -*- coding: utf-8 -*-
from web3 import Web3
import time
import requests

# Connect to the Monad network via Infura RPC
infura_url = "https://unichain-mainnet.g.alchemy.com/v2/5Gk_rxXVG6dSEK6B6AvSduc0IRbnYyr-"
web3 = Web3(Web3.HTTPProvider(infura_url, request_kwargs={'timeout': 60}))

# Check if the connection is successful
if not web3.is_connected():
    raise Exception("Failed to connect to Monad network")

# Constants
CHAIN_ID = 130  # Monad Chain ID
MAX_RETRIES = 5  # Maximum retries per transaction
RETRY_DELAY = 3  # Seconds between retries
PRIVATE_KEY = ""  # Hardcoded private key (use with caution)
MAX_BALANCE_THRESHOLD = 0.1  # Skip wallets with balance greater than this

# Function to check the balance of a wallet
def check_balance(wallet_address):
    balance = web3.eth.get_balance(wallet_address)
    return web3.from_wei(balance, 'ether')

# Function to send ETH transaction to a wallet
def send_eth_transaction_to_wallet(private_key, amount, to_address):
    sender_address = web3.eth.account.from_key(private_key).address
    value_to_send = web3.to_wei(amount, 'ether')

    for attempt in range(MAX_RETRIES):
        try:
            nonce = web3.eth.get_transaction_count(sender_address)
            gas_price = web3.eth.gas_price * 1.1
            estimated_gas_limit = web3.eth.estimate_gas({
                'from': sender_address,
                'to': to_address,
                'value': value_to_send
            })
            gas_limit = int(estimated_gas_limit * 1.2)

            tx = {
                'nonce': nonce,
                'to': to_address,
                'value': value_to_send,
                'gas': gas_limit,
                'gasPrice': int(gas_price),
                'chainId': CHAIN_ID
            }

            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            print(f"Sent {amount} ETH to {to_address}. Tx Hash: {web3.to_hex(tx_hash)}")
            return True  # Successfully sent
        except requests.exceptions.HTTPError as e:
            print(f"HTTPError on attempt {attempt+1}: {e}")
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(5)
            else:
                print("Transaction failed after maximum retries.")
    return False

# Function to load wallet addresses from wallets.txt
def load_wallet_addresses(filename="wallets.txt"):
    with open(filename, "r") as file:
        wallets = [line.strip() for line in file.readlines()]
    return wallets

# Function to process wallets: check balance, send ETH if needed
def process_wallets(amount):
    wallets = load_wallet_addresses()
    sender_address = web3.eth.account.from_key(PRIVATE_KEY).address

    for wallet_number, to_address in enumerate(wallets, start=1):
        balance = check_balance(to_address)
        print(f"Wallet {wallet_number} ({to_address}) balance: {balance:.6f} ETH")

        # Skip wallet if balance is greater than 0.1 ETH
        if balance > MAX_BALANCE_THRESHOLD:
            print(f"Skipping wallet {wallet_number} ({to_address}), balance above {MAX_BALANCE_THRESHOLD} ETH.\n")
            continue

        # Check if wallet has already received the required amount
        if balance >= amount:
            print(f"Wallet {wallet_number} ({to_address}) already has {amount} ETH. Skipping.\n")
            continue

        # Send ETH and verify it was received
        if send_eth_transaction_to_wallet(PRIVATE_KEY, amount, to_address):
            for retry in range(MAX_RETRIES):
                time.sleep(RETRY_DELAY)  # Wait before checking balance again
                new_balance = check_balance(to_address)

                if new_balance >= amount:
                    print(f"âœ… Wallet {wallet_number} ({to_address}) successfully received {amount} ETH.\n")
                    break
                else:
                    print(f"ðŸ”„ Checking again... Wallet {wallet_number} balance: {new_balance:.6f} ETH")
            else:
                print(f"âš ï¸ Wallet {wallet_number} ({to_address}) did not receive ETH after {MAX_RETRIES} checks.\n")

# Get user input for the ETH amount
def get_user_input():
    amount = float(input("Enter the amount of ETH to send to each wallet: "))
    return amount

# Main execution
amount = get_user_input()
process_wallets(amount)
