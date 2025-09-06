#  Content Sentinel
**Transparent Moderation for Web 2.0**  
-----

## Introduction

Content Sentinel is a **community-driven moderation system** that combines AI, Blockchain, and QKD.

Think of it like this:

  * AI scans content for red flags.
  * The community (moderators) votes on what should happen.
  * Blockchain makes the decision process **tamper-proof**.
  * Quantum tech (simulated here) protects moderator communications.

-----

## 1\. System Overview

  * **AI Layer** – Detects toxicity, spam, or misinformation in text.
  * **Blockchain Layer** – Records votes on a content hash, keeps moderator reputations.
  * **Quantum Layer** – Simulates BB84 key exchange so that moderators could share keys securely.
  * **API Layer** – Ties it all together with endpoints like `/analyze`, `/vote`, `/content/{hash}`.

-----

## 2\. Installation Instructions

### Prerequisites

You’ll need a few things set up first:

  * Python 3.10 or newer
  * pip & virtualenv
  * Node.js + npm (for Ganache, the local blockchain)
  * Ganache CLI installed globally
  * Git

### Steps

1.  **Clone the repo**
   ```bash
     git clone git@github.com:advaithkatta/content-sentinel.git
     cd content-sentinel
   ```  
    
2.  **Create a virtual environment, activate it, and install dependencies**
 ```bash
    python3 -m venv venv
    source venv/bin/activate
 ```
    Each layer in this project has its own `requirements.txt`:

```bash
    pip install -r ai/requirements.txt
    pip install -r api/requirements.txt
    pip install -r chain/requirements.txt
    pip install -r quantum/requirements.txt
```
    Install Ganache (blockchain):
```bash
    npm install -g ganache
```

-----

## 3\. Instructions for the Demo

### Start Ganache

```bash
ganache -p 8545
```

When you open Ganache, you'll get 10 private keys. Choose any key and put it into your API .env and your blockchain .env:

```
RPC_URL=http://127.0.0.1:8545 # url where ganache is running
PRIVATE_KEY=0xabc... # one of your Ganache account keys
ABI_PATH=chain/ContentSentinel.abi.json
CHAIN_ID=1337
```

### Deploy the Contract

```bash
cd chain
python compile_deploy.py
```

This compiles the Solidity contract and deploys it to Ganache. It will print the contract address. 

```bash
compile_deploy.py 
env: http://127.0.0.1:8545 0xa963f9e77a938571b9fdcddbca9610aacc00e7ffbfa1a2783dc54a8cd3e5be3c 1337
Deployed at: **0x9e3F1C396cf03656eB8ad133dFaDBbDE16faD429**
```
Take this contract address and put it in your api .env 

Your environment variables for api .env should look like this:

```
RPC_URL=http://127.0.0.1:8545
CONTRACT_ADDR=**0x9e3F1C396cf03656eB8ad133dFaDBbDE16faD429**... # address printed in step 2
PRIVATE_KEY=0xabc... # one of your Ganache account keys
ABI_PATH=chain/ContentSentinel.abi.json
CHAIN_ID=1337
```

### Start the api fast API server

```bash
uvicorn api.app:app --reload
```

### Analyze Text

Use the following `curl` command to analyze text using the AI model:

```bash
curl -X POST http://127.0.0.1:8000/analyze \
-H "Content-Type: application/json" \
-d '{"content": "The sun orbits the earth, obviously."}'
```

You will get a hash specific to your content and analysis results on your input, including misinformation, spam (or ham if it's not spam), and toxicity scores.

```bash
{"content_hash":"5b1a464448141cd26d4cec9dad7beb590e546500734d3b38082bb8dbc5dc558e","analysis":{"toxicity":{"label":"toxic","score":0.0009294120245613158},"spam":{"label":"HAM","score":0.9999983310699463},"misinformation":{"label":"supported","score":0.9996740818023682,"evidence":{"score":0.9996740818023682,"evidence_title":"Counter-Earth","nli":{"label":"entailment","score":0.9996740818023682,"all_probs":[0.9996740818023682,0.00010787756036734208,0.0002181113959522918]}}}}}
```

### Vote and Get Tally

To simulate a moderator vote (in this simulation, your vote will count as 100 votes), use the `/vote` endpoint. 
Votes:
0 - Remove, 
1 - Label, 
2 - Allow

```bash

 curl -X POST http://127.0.0.1:8000/vote \
>     -H "Content-Type: application/json" \
>     -d '{"content_hash": "<hash>", "choice": <0|1|2>}'

 curl -X POST http://127.0.0.1:8000/vote \
>     -H "Content-Type: application/json" \
>     -d '{"content_hash": "5b1a464448141cd26d4cec9dad7beb590e546500734d3b38082bb8dbc5dc558e", "choice": 2}'

Output:
{"tx_hash":"0xeeb9ad88211692bbd036cf4fce98057766d670a3722eb925226ea399bb8733fd","status":1}
```

Then, to get the current tally for a content hash, use the `/content` endpoint:

```bash
curl http://127.0.0.1:8000/content/<hash>
curl http://127.0.0.1:8000/content/5b1a464448141cd26d4cec9dad7beb590e546500734d3b38082bb8dbc5dc558e
{"remove_votes":0,"label_votes":0,"allow_votes":100,"decision":3,"finalized":true}
```

### Quantum Layer

```bash
cd quantum
python qkd_sim.py

🔑 Simulating QKD...
Shared secret key established!

Alice → Bob (encrypted): gAAAAABou5allzBo-LY2y6mvg2DfuJKZtj2t-f_oAlWF8vMPFeEKaotw1-aOvg5VeC5zRMJOB1RsSKwSl5ZUFQIKmeQZeaVmXrCaGKIKCPbnY_uMb-QIX9PZEUewuFai1S-sXQH4aj0b
Bob received from Alice: I think this post should be removed.
Bob → Alice (encrypted): gAAAAABou5alrXTLtVIrhikjVaO6YdOg1fPVMdEouJDHJE8TuofwT8Ec7YpqUucs50hUB5jbGylZYoXtVs2k8Y2I5OfLJnzvSc1_VV9_0dsya7zm9kEdjyM=
Alice received from Bob: Agreed, let’s vote remove.

```
-----

## 4\. File Walkthrough

  * `chain/compile_deploy.py` → compiles and deploys the Solidity contract.
  * `api/app.py` → FastAPI service exposing moderation endpoints.
  * `ai/inference.py` → wraps HuggingFace models for text analysis.
  * `quantum/qkd_sim.py` → simulates the BB84 protocol for secure key exchange.

-----


## 6\. Troubleshooting

  * **ABI file not found** → check ABI_PATH location in .env file
  * **Dependency issues (like numpy vs qiskit)** → install only the versions in `requirements.txt`.
  * **Port already in use** → stop the old process or run Ganache on a new port.

-----

## 7\. Next Steps

  * Build a frontend UI so moderators don’t need curl.
  * Add more AI categories (hate speech, bias, deepfake detection).
  * Deploy contracts to Ethereum testnets like Sepolia.
  * Replace simulated quantum exchange with real APIs.
