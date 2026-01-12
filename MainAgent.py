import time
import os
import sys

# Add src to path so we can import components
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from components.LogWatcher import LogWatcher
from components.VisionProcessor import VisionProcessor
from components.EternalReturnAPI import EternalReturnAPI
from components.LocalLLMHandler import LocalLLMHandler

class MainAgent:
    def __init__(self):
        print("Initializing ERAIAdv Agent...")
        
        # 1. Initialize Components
        self.log_watcher = LogWatcher()
        self.vision = VisionProcessor(config_dir="config")
        self.api = EternalReturnAPI() # Keys loaded from .env
        self.llm = LocalLLMHandler()
        
        # State
        self.current_mode = "Unknown"
        self.current_region = "Unknown"
        self.participants = {} # nickname -> stats

    def run(self):
        print("Agent is running. Waiting for game events...")
        
        # Start Log Watcher
        self.log_watcher.open_log()

        try:
            while True:
                # 1. Check Logs
                events = self.log_watcher.check_updates()
                for event in events:
                    self.handle_log_event(event)

                # 2. Manual Trigger for testing (e.g., keypress) could go here
                # For now, we rely on Log events or manual logic.
                
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping Agent.")

    def handle_log_event(self, event):
        print(f"[Event] {event['type']}: {event['value']}")
        
        if event['type'] == 'matching_mode':
            self.current_mode = event['value']
            print(f"-> Detected Mode: {self.current_mode}")

        elif event['type'] == 'state_change':
            if event['value'] == 'loading_screen':
                print("-> Loading Screen Detected! Waiting 5s for screen to settle...")
                time.sleep(5)  # Wait for full load
                self.perform_scan()

    def perform_scan(self):
        print("\n--- Starting Vision Scan ---")
        
        # 1. Capture & OCR
        results = self.vision.scan_frame()
        if "error" in results:
            print(f"Vision Error: {results['error']}")
            return

        print(f"Scanned {len(results)} items.")

        # 2. Process Results
        # Group by player (e.g., player1_name, player1_char)
        players = {}
        for key, text in results.items():
            if not text: continue
            
            # key example: "player1_name", "target_enemy_name"
            if "_name" in key:
                p_id = key.replace("_name", "")
                if p_id not in players: players[p_id] = {}
                players[p_id]['name'] = text
            elif "_char" in key:
                p_id = key.replace("_char", "")
                if p_id not in players: players[p_id] = {}
                players[p_id]['char'] = text

        # 3. Fetch Stats for found players
        print(f"Found {len(players)} players. Fetching stats...")
        
        for p_id, info in players.items():
            name = info.get('name')
            char = info.get('char', 'Unknown')
            
            if not name: continue

            print(f"checking: {name} ({char})...")
            
            # API Call
            uid = self.api.get_user_id(name)
            if uid:
                stats = self.api.get_user_stats(uid)
                self.participants[name] = stats
                print(f"   -> Stats: {stats}")
                
                # TODO: Identify if this player is STRONG/WEAK based on stats
                # logic_here(stats)
            else:
                print("   -> User Not Found (OCR Error?)")

        print("--- Scan Complete ---")
        
        # 4. Agent Commentary
        if self.participants:
            print("Thinking (Consulting LLM)...")
            # Build a simple text summary for the LLM
            context = f"現在のモード: {self.current_mode}\n検出されたプレイヤー:\n"
            for name, stats in self.participants.items():
                if stats:
                    context += f"- 名前: {name}, 勝率: {stats.get('win_rate')}%, 平均キル: {stats.get('avg_kills')}\n"
                else:
                    context += f"- 名前: {name}, データなし\n"
            
            context += "\nこの状況でのアドバイスをください。"
            
            advice = self.llm.generate_commentary(context)
            print(f"\n[AI Advice]: {advice}\n")
        else:
            print("No participants data found to analyze.")

if __name__ == "__main__":
    agent = MainAgent()
    agent.run()
