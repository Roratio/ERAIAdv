import time
import os
import re

class LogWatcher:
    # Standard path for Eternal Return logs
    LOG_PATH = os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\NimbleNeuron\Eternal Return\Player.log")

    def __init__(self, log_path=None):
        self.log_path = log_path or self.LOG_PATH
        self.file_handle = None
        self.where = 0

    def open_log(self):
        try:
            self.file_handle = open(self.log_path, 'r', encoding='utf-8', errors='ignore')
            # Go to the end of the file to ignore past events
            self.file_handle.seek(0, 2)
            self.where = self.file_handle.tell()
            print(f"[LogWatcher] Watching log: {self.log_path}")
            return True
        except FileNotFoundError:
            print(f"[LogWatcher] Log file not found at: {self.log_path}")
            return False

    def check_updates(self):
        """
        Reads new lines from the log file.
        Returns a list of interesting events (dictionaries).
        """
        if not self.file_handle:
            if not self.open_log():
                return []

        events = []
        where = self.file_handle.tell()
        line = self.file_handle.readline()
        
        while line:
            # Analyze line content
            event = self._parse_line(line)
            if event:
                events.append(event)
            
            line = self.file_handle.readline()

        self.where = self.file_handle.tell()
        return events

    def _parse_line(self, line):
        """
        Parses a single log line to find key events.
        """
        line = line.strip()
        
        # 1. Matching Mode (Normal, Rank, Cobalt, etc.)
        # Example: GlobalUserData:SetMatchingMode userNum:12345 matchingMode:3 (Rank)
        # Note: The log format changes often, need robust regex or multiple patterns.
        # User provided snippet: "GlobalUserData:SetMatchingMode ... Invoked: Normal"
        if "GlobalUserData:SetMatchingMode" in line:
            match = re.search(r"Invoked:\s*(\w+)", line)
            if match:
                return {"type": "matching_mode", "value": match.group(1)}

        # 2. Match Region
        if "Selected MatchingRegion" in line:
            match = re.search(r"Selected MatchingRegion\s*:\s*(\w+)", line)
            if match:
                return {"type": "region", "value": match.group(1)}

        # 3. Game State (Entering Loading Screen / Match Start)
        # Often indicated by scene changes or specific network messages.
        if "SceneManager:LoadScene Loading" in line or "LoadScene: Loading" in line:
            return {"type": "state_change", "value": "loading_screen"}
        
        if "SceneManager:LoadScene Lobby" in line:
            return {"type": "state_change", "value": "lobby"}

        # 4. In-Game State (Match Started)
        # "GameClient created" often implies actual gameplay start
        if "GameClient created" in line:
             return {"type": "state_change", "value": "game_started"}

        return None

if __name__ == "__main__":
    watcher = LogWatcher()
    print("Tail-ing log file... (Ctrl+C to stop)")
    while True:
        events = watcher.check_updates()
        for e in events:
            print(f"New Event: {e}")
        time.sleep(1)
