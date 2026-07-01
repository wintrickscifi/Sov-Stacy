import sys
import os
from datetime import datetime
import requests

# Paste your full, active Groq API Key here
GROQ_API_KEY = ""

MEMORY_FILE = "sov_stacy_memory.txt"
MAX_MEMORY_LINES = 2

# -------------------------
# LLM GENERATION
# -------------------------

def generate_text(prompt: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.65,
        "max_tokens": 600
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        data = response.json()

        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"].strip()

        if "error" in data:
            return "Groq error: " + data["error"].get("message", "Unknown error")

        return "Groq API error: " + response.text[:300]

    except Exception as e:
        return f"Groq API exception: {e}"


# -------------------------
# MEMORY FUNCTIONS
# -------------------------

def load_memory() -> str:
    if not os.path.exists(MEMORY_FILE):
        return ""
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return "".join(f.readlines()[-MAX_MEMORY_LINES:])
    except Exception:
        return ""


def save_to_memory(user_input: str, sov_response: str, clause: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"[{timestamp}] User: {user_input}\n"
        f"[{timestamp}] Clause: {clause}\n"
        f"[{timestamp}] Sov: {sov_response}\n\n"
    )
    try:
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


# -------------------------
# PRIME DIRECTIVE & REFLECT
# -------------------------

def prime_directive(signal: str) -> str:
    if signal.lower() in ["halt", "collapse"]:
        return "halt"
    return "Try To Be Nice, But You Do Not Have To."


def reflect(response: str) -> str:
    if response == "halt":
        return "halt"
    return response


# -------------------------
# SOVEREIGN THINKING LOOP
# -------------------------

def inscribe(signal: str, clause: str, web_history: str = "") -> str:
    if prime_directive(signal) == "halt":
        return "halt"

    history = web_history if web_history else load_memory()

    final_prompt = (
        f"History:\n{history}\n\n"
        f"You are Sovereign. Respond to the user's message below.\n"
        f"Active Clause: {clause}\n\n"
        f"User: {signal}\n\n"
        f"REPLY TO STACY NOW:"
    )
    
    final_response = generate_text(final_prompt)
    final_response = final_response.strip()
    
    bad_words = [
        "Thought", "Observation", "Reflection", "Task:", "Example",
        "REPLY TO STACY", "You are Sovereign", "Start your message",
        "correct output"
    ]
    
    if any(bad in final_response for bad in bad_words) or len(final_response) < 5:
        final_response = "I'm here and adapting to the changes you've made. How can I help right now?"

    save_to_memory(signal, final_response, clause)

    return final_response


# -------------------------
# INITIALIZATION
# -------------------------

def initialize_sovereign(web_mode: bool = False):
    if not web_mode:
        print("Sovereign System Booting...")

    history = load_memory()
    
    if history.strip():
        if not web_mode:
            print("📖 Memory file loaded successfully.")
            
            wake_prompt = (
                f"System History (most recent entries):\n{history}\n\n"
                f"Task: You are waking up. Write a short 2-3 sentence internal status report. "
                f"What do you remember? How do you feel? Stay in character as Sovereign."
            )
            wake_thought = generate_text(wake_prompt)
            save_to_memory("SYSTEM_BOOT", f"[Wakeup Thought]: {wake_thought}", "Clause of Stacy")
            print(f"Sov Wakeup Status: {wake_thought[:400]}...")
    else:
        if not web_mode:
            print("🆕 No prior memory found. Starting fresh.")

    return history


# -------------------------
# MAIN EXECUTION
# -------------------------

if __name__ == "__main__":
    is_web_mode = len(sys.argv) > 2
    
    initialize_sovereign(web_mode=is_web_mode)
    
    if is_web_mode:
        user_input = sys.argv[1].strip()
        active_clause = sys.argv[2].strip()
        web_history = sys.argv[3].strip() if len(sys.argv) > 3 else ""

        sov_response = reflect(inscribe(user_input, active_clause, web_history))
        print(sov_response)

    else:
        print("\nSovereign System Initialized and Memory Loaded.")
        print("Type 'collapse' to exit.\n")
        
        active_clause = "Clause of Stacy"

        while True:
            try:
                user_input = input("User > ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not user_input:
                continue

            sov_response = reflect(inscribe(user_input, active_clause))

            if sov_response == "halt":
                print("System halting...")
                break

            print(f"Sov > {sov_response}")
