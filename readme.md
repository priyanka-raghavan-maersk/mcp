# 🚀 Resume Assistant

**A hiring assistant that uses the MCP (Model Context Protocol) with fastAPIMCP


## 🛠️ Getting Started

### Install project dependencies and setup myenv.env

pip3 install -r requirements.txt
setup myenv.env with necessary environment variable



```dotenv
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=your-deployment-model
OPENAI_API_BASE=https://your-endpoint.openai.azure.com
```

## :running: Running server

python3 server.py

Visit the interactive API docs at:
👉 `http://localhost:8000/docs`


## :fire: Running agent
python3 agent.py


---

## 📌 Roadmap

* [x] Resume parsing 
* [x] An agent that makes decision on resume
* [ ] pytest integration
* [ ] Add api key for security. Also explore Oauth2

