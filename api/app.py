import os, hashlib, json
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from web3 import Web3
from ai.inference import analyze_content

load_dotenv()
app = FastAPI(title="Content Sentinel API")

# Load env vars
RPC = os.getenv("RPC_URL", "http://127.0.0.1:8545")
CONTRACT_ADDR = os.getenv("CONTRACT_ADDR")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # two levels up from api/
ABI_PATH = os.path.join(BASE_DIR, "chain", "ContentSentinel.abi.json")

PK = os.getenv("PRIVATE_KEY")

# Web3 setup
w3 = Web3(Web3.HTTPProvider(RPC))
with open(ABI_PATH) as f:
    ABI = json.load(f)

contract = w3.eth.contract(address=Web3.to_checksum_address(CONTRACT_ADDR), abi=ABI)
acct = w3.eth.account.from_key(PK)

# Request models
class AnalyzeReq(BaseModel):
    content: str

class VoteReq(BaseModel):
    content_hash: str
    choice: int  # 0=Remove, 1=Label, 2=Allow

# Routes
@app.post("/analyze")
def analyze(req: AnalyzeReq):
    res = analyze_content(req.content)
    chash = hashlib.sha256(req.content.encode("utf-8")).hexdigest()
    return {"content_hash": chash, "analysis": res}

@app.post("/vote")
def vote(req: VoteReq):
    chash_bytes32 = Web3.to_bytes(hexstr=req.content_hash)
    nonce = w3.eth.get_transaction_count(acct.address)
    tx = contract.functions.vote(chash_bytes32, req.choice).build_transaction({
        "from": acct.address,
        "nonce": nonce,
        "gas": 400000
    })
    signed = acct.sign_transaction(tx)
    txh = w3.eth.send_raw_transaction(signed.rawTransaction)
    rec = w3.eth.wait_for_transaction_receipt(txh)
    return {"tx_hash": rec.transactionHash.hex(), "status": rec.status}

@app.get("/content/{content_hash}")
def content_status(content_hash: str):
    chash_bytes32 = Web3.to_bytes(hexstr=content_hash)
    t = contract.functions.getTally(chash_bytes32).call()
    return {
        "remove_votes": t[0], "label_votes": t[1], "allow_votes": t[2],
        "decision": t[3], "finalized": t[4]
    }

# ✅ Entry point to run as server
#if __name__ == "__main__":
#    import uvicorn
#    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)