import requests
import json
import os

class LocalLLMHandler:
    DEFAULT_MODEL = "llama3"
    OLLAMA_URL = "http://localhost:11434/api/chat"

    def __init__(self, model_name=None):
        self.model = model_name or os.getenv("OLLAMA_MODEL", self.DEFAULT_MODEL)
        print(f"[LocalLLM] Initialized using model: {self.model}")

    def generate_commentary(self, context_text):
        """
        Sends context to the LLM and returns the generated advice/commentary.
        """
        prompt = self._build_system_prompt()
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": context_text}
            ],
            "stream": False
        }

        try:
            response = requests.post(self.OLLAMA_URL, json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            else:
                print(f"[LocalLLM] Error: {response.status_code} - {response.text}")
                return "（思考中...エラーが発生しました）"
        except Exception as e:
            print(f"[LocalLLM] Connection Error: {e}")
            return "（Ollamaに接続できません。起動していますか？）"

    def _build_system_prompt(self):
        return (
            "You are an AI assistant for the game 'Eternal Return'. "
            "Your role is to provide strategic advice and commentary based on the current match status. "
            "Speak in Japanese, be concise, and act like a knowledgeable coach or partner. "
            "If an enemy has a high win rate (>20%), warn the user. "
            "If an enemy is weak, encourage the user to attack."
        )

if __name__ == "__main__":
    # Test
    llm = LocalLLMHandler()
    print("Testing LLM...")
    response = llm.generate_commentary("敵プレイヤー: Hideonbush (Rio), 勝率25%, キル平均 3.5。どう動くべき？")
    print(f"Response: {response}")
