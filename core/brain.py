import re
import yaml
import ollama
from core.network import is_online
from spidy.system_prompt import build_system_prompt

with open("config.yaml") as f:
    config = yaml.safe_load(f)

BRAIN = config["brain"]


class Brain:
    def __init__(self, show_thinking: bool = False):
        self.system_prompt = build_system_prompt("config.yaml")
        self.temperature   = BRAIN["temperature"]
        self.show_thinking = show_thinking
        self._select_model()

    def _select_model(self):
        if is_online():
            self.model = BRAIN["cloud_model"]
            print(f"[Brain] Online — using {self.model}")
        else:
            self.model = BRAIN["local_model"]
            print(f"[Brain] Offline — using {self.model}")

    def chat(self, history: list, on_token=None) -> str:
        modified_history = []
        for i, msg in enumerate(history):
            if i == len(history) - 1 and msg["role"] == "user":
                modified_history.append({
                    "role"   : "user",
                    "content": (
                        msg["content"] +
                        "\n[Reply in plain text only. No JSON. No code blocks. No brackets.]"
                    )
                })
            else:
                modified_history.append(msg)

        messages      = [{"role": "system", "content": self.system_prompt}] + modified_history
        full_response = ""
        in_thinking   = False
        thinking_buf  = ""

        try:
            stream = ollama.chat(
                model   = self.model,
                messages= messages,
                stream  = True,
                options = {"temperature": self.temperature}
            )

            for chunk in stream:
                token = chunk["message"]["content"]

                # Detect thinking block start
                if "<think>" in token or "Thinking..." in token:
                    in_thinking = True
                    if self.show_thinking:
                        thinking_buf = "🤔 "
                    continue

                # Detect thinking block end
                if "</think>" in token or "...done thinking." in token:
                    in_thinking = False
                    if self.show_thinking and thinking_buf.strip():
                        print(f"\033[90m{thinking_buf.strip()}\033[0m\n")
                    thinking_buf = ""
                    continue

                if in_thinking:
                    if self.show_thinking:
                        thinking_buf += token
                    continue

                full_response += token
                if on_token:
                    on_token(token)

        except Exception as e:
            if self.model != BRAIN["local_model"]:
                print(f"[Brain] Cloud failed ({e}), switching to local...")
                self.model = BRAIN["local_model"]
                return self.chat(history, on_token)
            else:
                full_response = "Sorry anna, both models failed. Please check Ollama."

        return full_response.strip()