# 🛡️ Content Sentinel  
**Transparent Moderation for Web 2.0**  

Content Sentinel is a **community-driven moderation system** that combines:  
- 🤖 **AI Layer** → Detects toxicity, spam, and misinformation in user content  
- ⛓️ **Blockchain Layer** → Records moderation votes on Ethereum for transparency  
- ⚛️ **Quantum Layer** → Demonstrates secure communication using BB84 QKD  

This project is both a **working prototype** and a **research experiment** into hybrid moderation systems.  

---

## 🚀 Features
- FastAPI backend for content analysis and voting  
- Hugging Face NLP models (toxicity, spam, misinformation)  
- Solidity smart contract for voting & decision tallying  
- Ganache-powered local Ethereum blockchain  
- Quantum key distribution (BB84) demo using Qiskit  

---


## ⚙️ Installation

### 📋 Prerequisites
Before installation, make sure you have:
- **Python 3.10+**  
- **pip** and **venv**  
- **Node.js & npm** (for Ganache CLI)  
- **Git** installed  
- **Ganache CLI** (for local Ethereum)  
  ```bash
  npm install -g ganache

🛠️ Steps



## 📂 Project Structure
```bash
content-sentinel/
├─ api/            # FastAPI service (content ingest, AI calls, chain ops)
├─ ai/             # AI inference models
├─ chain/          # Solidity contracts + deploy scripts
├─ quantum/        # QKD simulation (BB84)
├─ web/            # Demo frontend
├─ docker/         # Dockerfiles + docker-compose.yml
└─ README.md

---


curl -X POST http://127.0.0.1:8000/analyze \
-H "C>     -H "Content-Type: application/json" \
>     -d '{"content": "The sun orbits the earth."}'

{"content_hash":"6e116857033694cded64acea7feafcf845e2da20dbc55a9e3319041d0637efb8","analysis":{"toxicity":{"label":"toxic","score":0.0009870171779766679},"spam":{"label":"HAM","score":0.9999983310699463},"misinformation":{"label":"supported","score":0.9977899789810181,"evidence":{"score":0.9977899789810181,"evidence_title":"High Earth orbit","nli":{"label":"entailment","score":0.9977899789810181,"all_probs":[0.9977899789810181,0.0009462605230510235,0.0012637831969186664]}}}}}


curl -X POST http://127.0.0.1:8000/vote \
>     -H "Content-Type: application/json" \
>     -d '{"content_hash": "6e116857033694cded64acea7feafcf845e2da20dbc55a9e3319041d0637efb8", "choice": 2}'
{"tx_hash":"0xa37a42bfe70f4684987f16b442f1fab239a2cc2b86ced2ec19b054dde09d1858","status":1}


curl http://127.0.0.1:8000/content/6e116857033694cded64acea7feafcf845e2da20dbc55a9e3319041d0637efb8
{"remove_votes":0,"label_votes":0,"allow_votes":100,"decision":3,"finalized":true}




  Transaction: 0x4e5945d25337895ca3f9273d5faa7b860cdca396108bfd335eef103f71e2dc9b
  Contract created: 0x330c0696049fd7930dd16c0f246531efb289407f
  Gas usage: 986703
  Block number: 1
  Block time: Thu Sep 04 2025 21:20:55 GMT-0400 (Eastern Daylight Time)


  Transaction: 0xa37a42bfe70f4684987f16b442f1fab239a2cc2b86ced2ec19b054dde09d1858
  Gas usage: 104273
  Block number: 2
  Block time: Thu Sep 04 2025 21:24:22 GMT-0400 (Eastern Daylight Time)






