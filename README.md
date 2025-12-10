# STUDY-ASSISTANT_Langgraph
# AI-Powered Study Assistant with LangGraph and Gemini

This project implements an **AI-powered study assistant** for Computer Science (AI/ML) topics using **LangGraph**, **LangChain**, and **Google Generative AI (Gemini)**. The assistant provides step-by-step explanations, runnable code snippets, and maintains conversation memory through summarization.

## Features
- **Conversational AI**: Handles multi-turn conversations with memory.
- **Summarization**: Compresses long conversations into concise summaries.
- **Runnable Code Examples**: Provides executable Python snippets when requested.
- **Transcript Logging**: Saves conversation logs in both text and JSONL formats.
- **Graph-based Workflow**: Uses LangGraph to manage conversation flow.

## Tech Stack
- Python 3.10+
- [LangChain](https://www.langchain.com/)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Google Generative AI](https://ai.google.dev/)
- dotenv for environment variable management

## Setup Instructions
1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/ai-study-assistant.git
   cd ai-study-assistant
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Create a `.env` file in the project root.
   - Add your Google Generative AI API key:
     ```env
     GOOGLE_API_KEY=your_api_key_here
     ```

4. **Run the assistant:**
   ```bash
   python main.py
   ```

## Usage
- Type your questions related to Computer Science or AI/ML.
- Type `exit` to quit the session.
- Conversation logs will be saved in `logging.txt` and `logging.jsonl`.

## File Structure
```
├── main.py              # Core script implementing the assistant
├── logging.txt          # Human-readable conversation log
├── logging.jsonl        # Structured log for analysis/replay
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Contribution Guidelines
1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Submit a pull request with a clear description of changes.

## License
This project is licensed under the MIT License.
