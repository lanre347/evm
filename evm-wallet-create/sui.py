from mnemonic import Mnemonic

def generate_mnemonic():
    mnemo = Mnemonic("english")
    words = mnemo.generate(strength=128)  # 128 bits = 12 words
    return words

def save_mnemonics_to_file(filename, count):
    with open(filename, "w") as f:
        for _ in range(count):
            mnemonic = generate_mnemonic()
            f.write(f"{mnemonic}\n")
    print(f"{count} Sui-compatible mnemonics saved to {filename}")

if __name__ == "__main__":
    num_wallets = int(input("Enter number of wallets to generate: "))
    save_mnemonics_to_file("wallets.txt", num_wallets)

#pip install mnemonic
