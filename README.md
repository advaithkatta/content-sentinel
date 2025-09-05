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
