from eth_account import Account

def generate_wallets(input_file="private_keys.txt", output_file="wallets.txt"):
    with open(input_file, "r") as f:
        private_keys = [line.strip() for line in f.readlines()]
    
    with open(output_file, "w") as f:
        for private_key in private_keys:
            account = Account.from_key(private_key)  # Generate wallet from private key
            f.write(account.address + "\n")  # Save only the address
    
    print(f"{len(private_keys)} wallet addresses saved to {output_file}")

if __name__ == "__main__":
    generate_wallets()
