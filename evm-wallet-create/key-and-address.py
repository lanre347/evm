from eth_account import Account
import secrets

def generate_wallet():
    private_key = "0x" + secrets.token_hex(32)
    account = Account.from_key(private_key)
    return account.address, private_key

def save_wallets_to_file(filename, count):
    with open(filename, "w") as f:
        for _ in range(count):
            address, private_key = generate_wallet()
            f.write(f"Address: {address}\nPrivate Key: {private_key}\n\n")
    print(f"{count} wallets generated and saved to {filename}")

if __name__ == "__main__":
    num_wallets = int(input("Enter number of wallets to generate: "))
    save_wallets_to_file("wallets.txt", num_wallets)
