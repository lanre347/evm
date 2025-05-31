from eth_account import Account

# Enable mnemonic (HD wallet) features
Account.enable_unaudited_hdwallet_features()

def generate_mnemonic():
    acct, mnemonic = Account.create_with_mnemonic()
    return mnemonic

def save_mnemonics_to_file(filename, count):
    with open(filename, "w") as f:
        for _ in range(count):
            mnemonic = generate_mnemonic()
            f.write(mnemonic + "\n")
    print(f"{count} mnemonics generated and saved to {filename}")

if __name__ == "__main__":
    num_wallets = int(input("Enter number of wallets to generate: "))
    save_mnemonics_to_file("mnemonic.txt", num_wallets)
