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
MAX_RETRIES = 5   # Maximum retries per transaction
RETRY_DELAY = 3  # Seconds between retries
PRIVATE_KEY = ""  # Hardcoded private key (use with caution)

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
            tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"âœ… Sent {amount} ETH to {to_address}. Tx Hash: {web3.to_hex(tx_hash)}")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"HTTPError on attempt {attempt+1}: {e}")
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                print("âŒ Transaction failed after maximum retries.")
    return False

# Function to load wallet addresses from wallets.txt
def load_wallet_addresses(filename="wallets.txt"):
    with open(filename, "r") as file:
        wallets = [line.strip() for line in file.readlines()]
    return wallets

# Function to send ETH to each wallet (without balance check)
def process_wallets(amount):
    wallets = load_wallet_addresses()
    sender_address = web3.eth.account.from_key(PRIVATE_KEY).address
    print(f"Sender address: {sender_address}\n")

    for wallet_number, to_address in enumerate(wallets, start=1):
        print(f"ðŸ” Sending to wallet {wallet_number}: {to_address}")
        send_eth_transaction_to_wallet(PRIVATE_KEY, amount, to_address)
        time.sleep(3)  # Optional pause between sends

# Get user input for the ETH amount
def get_user_input():
    try:
        amount = float(input("Enter the amount of ETH to send to each wallet: "))
        return amount
    except ValueError:
        print("Invalid input. Please enter a numeric value.")
        return get_user_input()

# Main execution
amount = get_user_input()
process_wallets(amount)
