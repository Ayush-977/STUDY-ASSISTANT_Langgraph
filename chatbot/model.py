from typing import TypedDict, List, Optional
from datetime import datetime
import json
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

load_dotenv()

class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]
    summary: Optional[str]  

# Instantiate the model
# You can configure temperature/top_p, safety settings if needed.
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# normalize content to string
def _to_str_content(msg: BaseMessage) -> str:
    """
    Some users return content as lists or structured parts.
    This function normalizes to a string for printing/logging.
    """
    content = getattr(msg, "content", "")
    if isinstance(content, str):#if content is a str
        return content
    if isinstance(content, list):#if content is a list
        # Concatenate text parts if present
        return "\n".join(str(p) for p in content if p is not None)
    return str(content)

MAX_MESSAGES_BEFORE_SUMMARY = 12   # when history gets long, summarize it
KEEP_LAST_MESSAGES = 6             # keep the latest few messages alongside the summary

# 6) Node: process — call LLM with current context + optional summary
def process(state: AgentState) -> AgentState:
    """
    Core node: takes the message history, adds a summary (if present),
    calls the LLM, and returns the updated state.
    """
    msgs = state.get("messages", [])
    summary = state.get("summary")

    # Building the input for the model: include system instructions, summary (if any), and history.
    system_prompt = SystemMessage(content=(
        "You are an AI-powered study assistant for Computer Science (AI/ML). "
        "Explain step-by-step with clear examples. If coding is requested, provide runnable snippets. "
        "Be concise but helpful."
    ))

    augmented: List[BaseMessage] = [system_prompt]
    if summary:
        augmented.append(SystemMessage(content=f"Conversation summary so far:\n{summary}"))

    augmented.extend(msgs)

    try:
        response: BaseMessage = llm.invoke(augmented)
    except Exception as e:
        # Return a helpful AIMessage on failure
        error_text = f"Sorry, I ran into an error while generating a response: {e}"
        response = AIMessage(content=error_text)

    # Immutable update: create a new list with the response appended
    new_messages = msgs + [response]

    print(f"\nAI: {_to_str_content(response)}")
    print(f"CURRENT STATE: {len(new_messages)} messages (summary={'yes' if summary else 'no'})")

    # Decide whether we should summarize next
    return {"messages": new_messages, "summary": summary}

# summarize — compress the conversation into a short memory string
def summarize(state: AgentState) -> AgentState:
    """
    Summarize the conversation so far into a short bullet list memory.
    Then trim the message history to keep only the last few messages.
    """
    msgs = state.get("messages", [])
    prev_summary = state.get("summary", "")

    # Building a summarization request
    summarizer_prompt = [
        SystemMessage(content=(
            "You are a helpful assistant. Summarize the conversation so far into a short memory "
            "that captures goals, key facts, decisions, and unresolved questions. Keep it concise, "
            "bullet style, no fluff. If there's an existing summary, update/merge it."
        ))
    ] + msgs

    try:
        summary_resp: BaseMessage = llm.invoke(summarizer_prompt)
        new_summary_text = _to_str_content(summary_resp).strip()
    except Exception as e:
        new_summary_text = f"(Summarization failed: {e})"

    # Merge with previous summary if any
    merged_summary = (prev_summary + "\n" + new_summary_text).strip() if prev_summary else new_summary_text

    # Trim messages: keep only the latest few, plus a system note that is summarized
    trimmed_messages = msgs[-KEEP_LAST_MESSAGES:] if len(msgs) > KEEP_LAST_MESSAGES else msgs
    # Add an informational system message to reflect summarization 
    info_note = SystemMessage(content="(Context compressed: earlier conversation summarized.)")
    new_messages = [info_note] + trimmed_messages

    print("\n[Memory] Conversation summarized and history trimmed.")
    return {"messages": new_messages, "summary": merged_summary}

# Router: decide whether to summarize or end
def should_summarize(state: AgentState) -> str:
    msgs = state.get("messages", [])
    # Count only human+ai messages (ignore system notes)
    count = sum(1 for m in msgs if m.type in ("human", "ai"))
    return "summarize" if count >= MAX_MESSAGES_BEFORE_SUMMARY else "end"

# Building the graph
graph = StateGraph(AgentState)
graph.add_node("process", process)
graph.add_node("summarize", summarize)

graph.add_edge(START, "process")
graph.add_conditional_edges("process", should_summarize, {
    "summarize": "summarize",
    "end": END,
})
graph.add_edge("summarize", END)

agent = graph.compile()

# Transcript saving
def save_transcript(messages: List[BaseMessage], summary: Optional[str]):
    with open("logging.txt", "w", encoding="utf-8") as file:
        file.write("Your Conversation Log:\n")
        if summary:
            file.write("\n[Summary]\n")
            file.write(summary + "\n\n")
        for m in messages:
            role = m.type  
            content = _to_str_content(m)
            if role == "human":
                file.write(f"You: {content}\n")
            elif role == "ai":
                file.write(f"AI: {content}\n\n")
            elif role == "system":
                file.write(f"[System]: {content}\n")
        file.write("End of Conversation\n")

    # Structured JSONL for analysis/replay
    timestamp = datetime.utcnow().isoformat() + "Z"
    with open("logging.jsonl", "w", encoding="utf-8") as jf:
        for m in messages:
            jf.write(json.dumps({
                "ts": timestamp,
                "role": m.type,           
                "content": _to_str_content(m),
            }, ensure_ascii=False) + "\n")
        if summary:
            jf.write(json.dumps({
                "ts": timestamp,
                "role": "system",
                "content": f"[SUMMARY]\n{summary}",
            }, ensure_ascii=False) + "\n")

# REPL loop
def main():
    print("Type 'exit' to quit.\n")

    # Initialize conversation with a system prompt
    system_prompt = SystemMessage(content=(
        "You are a helpful, step-by-step assistant. "
        "Explain CS/AI topics clearly. If the user asks for code, provide runnable examples."
    ))

    conversation_state: AgentState = {"messages": [system_prompt], "summary": None}

    try:
        user_input = input("Enter: ").strip()
        while user_input.lower() != "exit":
            conversation_state["messages"].append(HumanMessage(content=user_input))

            # Invoke the graph with the current state
            result = agent.invoke(conversation_state)
            # Update entire state immutably
            conversation_state = {
                "messages": result["messages"],
                "summary": result.get("summary", conversation_state.get("summary"))
            }

            user_input = input("Enter: ").strip()

    except KeyboardInterrupt:
        print("\nInterrupted. Saving conversation...")
    finally:
        save_transcript(conversation_state["messages"], conversation_state.get("summary"))
        print("Conversation saved to logging.txt and logging.jsonl")


if __name__ == "__main__":
    main()
