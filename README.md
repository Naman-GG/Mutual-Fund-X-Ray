# 📈 ET MoneyMentor Pro

ET MoneyMentor Pro is an advanced, multi-agent Mutual Fund Portfolio X-Ray engine built for the **Economic Times AI Hackathon**. Powered by LangGraph and Gemini 2.5 Flash, it autonomously decodes complex CAMS/KFintech Consolidated Account Statements (CAS), calculates true Extended Internal Rate of Return (XIRR) via `pyxirr`, and generates highly personalized rebalancing strategies against trailing market benchmarks.

## 🚀 Key Features

*   **Agentic Pipeline**: Employs a multi-actor LangGraph state machine (Extractor -> Analyst -> Strategist) to divide and conquer financial intelligence logic.
*   **CAS Native Decryption**: Upload and securely decrypt CAMS/KFintech PDFs locally using the `casparser` engine without exposing raw data to the cloud.
*   **Algorithmic XIRR**: Traverses your precise transaction-level cash flows matched with high-speed Rust-based XIRR calculations to calculate your true trailing returns.
*   **Pro-Max UI Engine**: Built on local Streamlit but deeply injected with strict UI/UX Pro Max glassmorphism structural laws, ensuring an elite tracking experience.
*   **Overlap Detection**: Automatically alerts you to dangerous duplicate underlying stock overheads disguised across varying mutual fund wrapper names.

---

## 🛠️ Local Installation & Setup

Follow these steps exactly to deploy ET MoneyMentor Pro optimally on your local machine.

### 1. Clone the Repository
Clone the project directly from GitHub and enter the local directory.
```bash
git clone <your-repository-url>
cd ET_GenAI
```

### 2. Set Up a Virtual Environment (Highly Recommended)
Isolate your dependencies to avoid interfering with system Python packages.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Required Dependencies
Install all the necessary backend packages (`streamlit`, `langgraph`, `casparser`, `pyxirr`, etc.).
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
The overarching AI Strategist requires a modern **Gemini API Key**.

1. Copy the provided environment template to a functional `.env` file:
   **macOS / Linux:**
   ```bash
   cp .env.example .env
   ```
   **Windows:**
   ```powershell
   copy .env.example .env
   ```

2. Open the new `.env` file and replace the placeholder text with your actual generated API key. You can generate a free key instantly from [Google AI Studio](https://aistudio.google.com/app/apikey):
   ```env
   GOOGLE_API_KEY="AIzaSy...your_actual_key..."
   ```

### 5. Launch the Engine
Boot the Streamlit Application Server.
```bash
streamlit run app.py
```
> The application will automatically execute and bridge to your default web browser at `http://localhost:8501`.

---

## 📂 Architecture Overview
*   **`app.py`**: The Streamlit interface, Glassmorphism CSS, and Flexbox metric architecture.
*   **`workflow.py`**: Constructs and orchestrates the LangGraph Directed Acyclic Graph.
*   **`agents.py`**: The underlying brains containing all Gemini LLM structured parsing, `pyxirr` analytics, and evaluation logic.
*   **`schema.py`**: Defines strict Pydantic typed-schemas protecting the data flow between arbitrary AI agents.
*   **`market_data.csv`**: A local snapshot database containing mappings of over 50+ leading Indian Mutual Funds spanning various market caps.
