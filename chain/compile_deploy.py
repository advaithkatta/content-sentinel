import json, os
from web3 import Web3
from solcx import compile_standard, install_solc
from dotenv import load_dotenv
load_dotenv()

RPC = os.getenv("RPC_URL", "http://127.0.0.1:8545")
PK  = os.getenv("PRIVATE_KEY")
CHAIN_ID = int(os.getenv("CHAIN_ID", "1337"))

print("env:", RPC,PK,CHAIN_ID)

with open("contracts/ContentSentinel.sol") as f:
    source = f.read()

install_solc("0.8.24")
compiled = compile_standard({
    "language":"Solidity",
    "sources":{"ContentSentinel.sol":{"content":source}},
    "settings":{"outputSelection":{"*":{"*":["abi","evm.bytecode.object"]}}}
}, solc_version="0.8.24")

abi = compiled["contracts"]["ContentSentinel.sol"]["ContentSentinel"]["abi"]
bytecode = compiled["contracts"]["ContentSentinel.sol"]["ContentSentinel"]["evm"]["bytecode"]["object"]

w3 = Web3(Web3.HTTPProvider(RPC))
acct = w3.eth.account.from_key(PK)
nonce = w3.eth.get_transaction_count(acct.address)

ContentSentinel = w3.eth.contract(abi=abi, bytecode=bytecode)
tx = ContentSentinel.constructor().build_transaction({"from": acct.address, "nonce": nonce, "chainId": CHAIN_ID, "gas": 6_000_000})
signed = acct.sign_transaction(tx)
txh = w3.eth.send_raw_transaction(signed.rawTransaction)
receipt = w3.eth.wait_for_transaction_receipt(txh)
print("Deployed at:", receipt.contractAddress)

with open("ContentSentinel.abi.json","w") as f: json.dump(abi,f, indent=2)