# -*- coding: utf-8 -*-
from web3 import Web3
import time
import random
import requests
from datetime import datetime, timedelta

# Connect to Monad network
infura_url = "https://unichain-mainnet.g.alchemy.com/v2/5Gk_rxXVG6dSEK6B6AvSduc0IRbnYyr-"
web3 = Web3(Web3.HTTPProvider(infura_url, request_kwargs={'timeout': 60}))

if not web3.is_connected():
    raise Exception("Failed to connect to Monad network")

# Constants
CHAIN_ID = 130
MAX_RETRIES = 3
INTERVAL_MINUTES = 1380
PREVIOUS_CHOICE = None

# Load private keys from file
def load_private_keys(filename="keys.txt"):
    with open(filename, "r") as file:
        return [line.strip() for line in file.readlines()]

# Generate dummy contract/wallet addresses
def generate_random_contract_address():
    return Web3.to_checksum_address("0x" + "".join(random.choices("0123456789abcdef", k=40)))

def generate_random_wallet_address():
    return Web3.to_checksum_address("0x" + "".join(random.choices("0123456789abcdef", k=40)))

# Get ETH balance
def check_balance(private_key):
    address = web3.eth.account.from_key(private_key).address
    return web3.from_wei(web3.eth.get_balance(address), 'ether')

# Wait until transaction fee is below max limit
def wait_for_reasonable_fee(gas_limit, max_fee_eth):
    while True:
        gas_price = int(web3.eth.gas_price * 1.1)
        estimated_fee_eth = web3.from_wei(gas_limit * gas_price, 'ether')
        if estimated_fee_eth <= max_fee_eth:
            return gas_price
        print(f"Current estimated fee {estimated_fee_eth} ETH exceeds max of {max_fee_eth} ETH. Waiting...")
        time.sleep(15)

# Send ETH transaction with fixed amount
def send_eth_transaction(private_key, repetitions, amount, to_contracts=True, wallet_number=None, custom_to_address=None, max_tx_fee_eth=0.0002):
    sender = web3.eth.account.from_key(private_key).address
    value_to_send = web3.to_wei(amount, 'ether')
    balance = check_balance(private_key)

    print(f"Wallet {wallet_number} ({sender}) balance: {balance} ETH")
    if balance < amount:
        print("Insufficient balance. Skipping.")
        return

    for i in range(repetitions):
        to_address = Web3.to_checksum_address(custom_to_address) if custom_to_address else (
            generate_random_contract_address() if to_contracts else generate_random_wallet_address())

        for attempt in range(MAX_RETRIES):
            try:
                nonce = web3.eth.get_transaction_count(sender)
                gas_estimate = web3.eth.estimate_gas({'from': sender, 'to': to_address, 'value': value_to_send})
                gas_limit = int(gas_estimate * 1.2)
                gas_price = wait_for_reasonable_fee(gas_limit, max_tx_fee_eth)

                tx = {
                    'nonce': nonce,
                    'to': to_address,
                    'value': value_to_send,
                    'gas': gas_limit,
                    'gasPrice': gas_price,
                    'chainId': CHAIN_ID
                }

                signed_tx = web3.eth.account.sign_transaction(tx, private_key)
                tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                print(f"Transaction {i+1}/{repetitions} sent to {to_address} with {amount} ETH. Hash: {web3.to_hex(tx_hash)}")
                break
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
                if "insufficient funds" in str(e).lower():
                    return
                time.sleep(5)

        time.sleep(5)

# Send percentage of balance
def send_percentage_balance(private_key, percentage, wallet_number=None, custom_to_address=None, max_tx_fee_eth=0.0002):
    sender = web3.eth.account.from_key(private_key).address
    balance = web3.eth.get_balance(sender)

    try:
        dummy_value = 1
        estimated_gas = web3.eth.estimate_gas({'from': sender, 'to': custom_to_address, 'value': dummy_value})
        gas_limit = int(estimated_gas * 1.2)
        gas_price = wait_for_reasonable_fee(gas_limit, max_tx_fee_eth)
        tx_fee = gas_limit * gas_price

        amount_to_send = int(balance * (percentage / 100))
        if amount_to_send <= tx_fee:
            print(f"Wallet {wallet_number} can't send {percentage}% - too low after gas.")
            return

        value_to_send = amount_to_send - tx_fee
        if value_to_send <= 0:
            print(f"Wallet {wallet_number} not enough to send after gas.")
            return

        tx = {
            'nonce': web3.eth.get_transaction_count(sender),
            'to': Web3.to_checksum_address(custom_to_address),
            'value': value_to_send,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'chainId': CHAIN_ID
        }

        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Sent {percentage}% from wallet {wallet_number}. Tx: {web3.to_hex(tx_hash)}")
    except Exception as e:
        print(f"Wallet {wallet_number} failed: {e}")

# Automate based on user choice
def automate_daily_transfers():
    global PREVIOUS_CHOICE

    if PREVIOUS_CHOICE is None:
        print("\nSelect transaction type:")
        print("1: Send 0 ETH to random contracts")
        print("2: Send 0.00000001 ETH to random wallets")
        print("3: Send specific amount to a wallet")
        print("4: Send PERCENTAGE of balance to a wallet")
        PREVIOUS_CHOICE = input("Enter 1, 2, 3 or 4: ")
    else:
        print(f"Using previous choice: {PREVIOUS_CHOICE}")

    repetitions = 1
    custom_to_address = None
    private_keys = load_private_keys()
    max_fee_eth = float(input("Enter max transaction fee in ETH (e.g. 0.0002): "))

    if PREVIOUS_CHOICE == "4":
        custom_to_address = input("Enter wallet address to send percentage to: ")
        percentage = float(input("Enter percentage of balance to send (e.g. 50): "))
        for wallet_number, pk in enumerate(private_keys, start=1):
            send_percentage_balance(pk, percentage, wallet_number, custom_to_address, max_tx_fee_eth=max_fee_eth)
        return

    elif PREVIOUS_CHOICE == "3":
        custom_to_address = input("Enter the wallet address: ")
        amount = float(input("Enter amount in ETH: "))
        to_contracts = False
    elif PREVIOUS_CHOICE == "2":
        amount = 0.00000001
        to_contracts = False
    elif PREVIOUS_CHOICE == "1":
        amount = 0
        to_contracts = True
    else:
        print("Invalid choice.")
        return

    for wallet_number, pk in enumerate(private_keys, start=1):
        send_eth_transaction(
            pk, repetitions, amount,
            to_contracts=to_contracts,
            wallet_number=wallet_number,
            custom_to_address=custom_to_address if PREVIOUS_CHOICE == "3" else None,
            max_tx_fee_eth=max_fee_eth
        )

# Run once immediately
automate_daily_transfers()

# Re-run on interval
next_run = datetime.now() + timedelta(minutes=INTERVAL_MINUTES)
while True:
    now = datetime.now()
    if now >= next_run:
        automate_daily_transfers()
        next_run = now + timedelta(minutes=INTERVAL_MINUTES)
    remaining_time = next_run - now
    print(f"Next run in: {remaining_time.seconds // 60} min {remaining_time.seconds % 60} sec", end="\r")
    time.sleep(1)
