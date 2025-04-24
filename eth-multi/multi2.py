# -*- coding: utf-8 -*-
from web3 import Web3
import time
import random
import requests
from datetime import datetime, timedelta

# Connect to the Monad network via Infura RPC
infura_url = "https://unichain-mainnet.g.alchemy.com/v2/5Gk_rxXVG6dSEK6B6AvSduc0IRbnYyr-"
web3 = Web3(Web3.HTTPProvider(infura_url, request_kwargs={'timeout': 60}))

# Check if the connection is successful
if not web3.is_connected():
    raise Exception("Failed to connect to Monad network")

# Constants
CHAIN_ID = 130  # Monad Chain ID
MAX_RETRIES = 3  # Maximum retries per transaction
INTERVAL_MINUTES = 1380  # Interval in minutes for automatic execution
PREVIOUS_CHOICE = None  # Store the previous choice

# Function to generate a random contract address
def generate_random_contract_address():
    return Web3.to_checksum_address("0x" + "".join(random.choices("0123456789abcdef", k=40)))

# Function to generate a random wallet address
def generate_random_wallet_address():
    random_address = "0x" + "".join(random.choices("0123456789abcdef", k=40))
    return Web3.to_checksum_address(random_address)

# Function to check the balance of a wallet
def check_balance(private_key):
    sender_address = web3.eth.account.from_key(private_key).address
    balance = web3.eth.get_balance(sender_address)
    balance_in_eth = web3.from_wei(balance, 'ether')
    return balance_in_eth

# Function to send ETH transaction
def send_eth_transaction(private_key, repetitions, amount, to_contracts=True, wallet_number=None, custom_to_address=None):
    sender_address = web3.eth.account.from_key(private_key).address
    value_to_send = web3.to_wei(amount, 'ether')

    # Check wallet balance
    balance_in_eth = check_balance(private_key)
    print(f"Wallet {wallet_number} ({sender_address}) balance: {balance_in_eth} ETH")

    if balance_in_eth < amount:
        print(f"Insufficient balance in wallet {wallet_number} ({sender_address}). Skipping.")
        return

    if wallet_number is not None:
        print(f"\nSending transactions from wallet {wallet_number} ({sender_address})")

    for i in range(repetitions):
        if custom_to_address:
            to_address = Web3.to_checksum_address(custom_to_address)
        else:
            to_address = generate_random_contract_address() if to_contracts else generate_random_wallet_address()

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
                print(f"Transaction {i+1}/{repetitions} sent to {to_address} with {amount} ETH! Tx Hash: {web3.to_hex(tx_hash)}")
                break
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
                if "insufficient balance" in str(e).lower():
                    return
                if attempt < MAX_RETRIES - 1:
                    time.sleep(5)
                else:
                    print("Max retries reached. Skipping.")
                    return

        time.sleep(5)

    print(f"Completed for wallet {wallet_number}: {sender_address}!\n")

# Function to automate daily transfers
def automate_daily_transfers():
    global PREVIOUS_CHOICE
    if PREVIOUS_CHOICE is None:
        print("Select transaction type for today:")
        print("1: Send 0 ETH to random contracts")
        print("2: Send 0.0001 ETH to random wallets")
        print("3: Send to a specific wallet address")
        PREVIOUS_CHOICE = input("Enter 1, 2 or 3: ")
    else:
        print(f"Using previous choice: {PREVIOUS_CHOICE}")

    repetitions = 1
    custom_to_address = None

    if PREVIOUS_CHOICE == "3":
        custom_to_address = input("Enter the wallet address to send to: ")
        amount = float(input("Enter amount in ETH to send: "))
        to_contracts = False
    elif PREVIOUS_CHOICE == "2":
        amount = 0.0001
        to_contracts = False
    elif PREVIOUS_CHOICE == "1":
        amount = 0
        to_contracts = True
    else:
        print("Invalid choice.")
        return

    private_keys = load_private_keys()

    for wallet_number, private_key in enumerate(private_keys, start=1):
        send_eth_transaction(
            private_key,
            repetitions,
            amount,
            to_contracts=to_contracts,
            wallet_number=wallet_number,
            custom_to_address=custom_to_address if PREVIOUS_CHOICE == "3" else None
        )

# Function to load private keys from keys.txt
def load_private_keys(filename="keys.txt"):
    with open(filename, "r") as file:
        private_keys = [line.strip() for line in file.readlines()]
    return private_keys

# Initiate the first transaction immediately
automate_daily_transfers()

# Schedule the function to run at a set interval
next_run = datetime.now() + timedelta(minutes=INTERVAL_MINUTES)
while True:
    now = datetime.now()
    if now >= next_run:
        automate_daily_transfers()
        next_run = now + timedelta(minutes=INTERVAL_MINUTES)
    remaining_time = next_run - now
    print(f"Next transaction in: {remaining_time.seconds // 60} minutes and {remaining_time.seconds % 60} seconds", end="\r")
    time.sleep(1)
