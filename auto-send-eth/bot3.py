# -*- coding: utf-8 -*-
from web3 import Web3
import time
import requests

# Connect to the Monad network via Infura RPC
infura_url = "https://unichain-mainnet.g.alchemy.com/v2/5Gk_rxXVG6dSEK6B6AvSduc0IRbnYyr-"
web3 = Web3(Web3.HTTPProvider(infura_url, request_kwargs={'timeout': 60}))

# Check connection
if not web3.is_connected():
    raise Exception("Failed to connect to Monad network")

# Constants
CHAIN_ID = 130
MAX_RETRIES = 5
RETRY_DELAY = 3
GAS_WAIT_INTERVAL = 5  # Seconds between fee checks
PRIVATE_KEY = ""  # ?? Use with caution

# Get user-defined max transaction fee in ETH
def get_max_transaction_fee_eth():
    user_input = input("Enter max transaction fee in ETH (e.g. 0.0001): ").strip()
    try:
        return float(user_input)
    except ValueError:
        print("Invalid input. Please enter a decimal ETH value.")
        return get_max_transaction_fee_eth()

# Wait until total estimated fee is acceptable
def wait_for_transaction_fee_limit(gas_limit, max_fee_eth):
    while True:
        gas_price = web3.eth.gas_price
        estimated_fee_eth = Web3.from_wei(gas_price * gas_limit, 'ether')
        if estimated_fee_eth <= max_fee_eth:
            return gas_price
        print(f"âŒ Estimated fee {estimated_fee_eth:.10f} ETH too high (max {max_fee_eth} ETH). Waiting...")
        time.sleep(GAS_WAIT_INTERVAL)

# Send ETH transaction
def send_eth_transaction_to_wallet(private_key, amount, to_address, max_fee_eth):
    sender_address = web3.eth.account.from_key(private_key).address
    value_to_send = web3.to_wei(amount, 'ether')

    for attempt in range(MAX_RETRIES):
        try:
            nonce = web3.eth.get_transaction_count(sender_address)

            # Estimate gas limit
            estimated_gas_limit = web3.eth.estimate_gas({
                'from': sender_address,
                'to': to_address,
                'value': value_to_send
            })
            gas_limit = int(estimated_gas_limit * 1.2)

            # Wait for acceptable fee
            gas_price = wait_for_transaction_fee_limit(gas_limit, max_fee_eth)

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

# Load wallet addresses
def load_wallet_addresses(filename="wallets.txt"):
    with open(filename, "r") as file:
        return [line.strip() for line in file.readlines()]

# Process each wallet
def process_wallets(amount, max_fee_eth):
    wallets = load_wallet_addresses()
    sender_address = web3.eth.account.from_key(PRIVATE_KEY).address
    print(f"Sender address: {sender_address}\n")

    for wallet_number, to_address in enumerate(wallets, start=1):
        print(f"ðŸ” Sending to wallet {wallet_number}: {to_address}")
        send_eth_transaction_to_wallet(PRIVATE_KEY, amount, to_address, max_fee_eth)
        time.sleep(3)

# Get ETH amount input
def get_user_amount():
    try:
        return float(input("Enter the amount of ETH to send to each wallet: "))
    except ValueError:
        print("Invalid input. Please enter a number.")
        return get_user_amount()

# Main
if __name__ == "__main__":
    amount = get_user_amount()
    max_fee_eth = get_max_transaction_fee_eth()
    process_wallets(amount, max_fee_eth)
