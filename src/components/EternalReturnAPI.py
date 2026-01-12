import requests
import json
import os

class EternalReturnAPI:
    BASE_URL = "https://open-api.bser.io"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("ER_API_KEY")
        if not self.api_key:
            print("[Warning] ER_API_KEY is not set. API calls will fail.")
        
        self.headers = {
            "x-api-key": self.api_key,
            "accept": "application/json"
        }
        # Simple in-memory cache for nickname -> userNum
        self.user_cache = {}

    def get_user_id(self, nickname):
        """
        Fetches userNum (userId) from nickname.
        Returns userNum (int) or None if not found/error.
        """
        if nickname in self.user_cache:
            return self.user_cache[nickname]

        url = f"{self.BASE_URL}/v1/user/nickname"
        params = {"query": nickname}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200:
                    user_num = data['user']['userNum']
                    self.user_cache[nickname] = user_num
                    return user_num
            elif response.status_code == 404:
                print(f"[API] User not found: {nickname}")
            else:
                print(f"[API] Error fetching user ID: {response.status_code} {response.text}")
        except Exception as e:
            print(f"[API] Exception in get_user_id: {e}")
        
        return None

    def get_user_stats(self, user_num, season_id=0):
        """
        Fetches stats for a user.
        season_id: 0 for normal games (or current season if specific API used).
        Note: The official API documentation might specify different endpoints for usage.
        Using /v1/user/games/{userNum} for recent history as a reliable fallback
        since V2 stats endpoints often require specific season IDs.
        """
        if not user_num:
            return None

        # Fetching recent games is often more useful for "current form"
        url = f"{self.BASE_URL}/v1/user/games/{user_num}"
        
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                if "userGames" in data:
                    return self._summarize_stats(data["userGames"])
            else:
                print(f"[API] Error fetching stats: {response.status_code}")
        except Exception as e:
            print(f"[API] Exception in get_user_stats: {e}")
        
        return None

    def _summarize_stats(self, games):
        """
        Summarizes the last 10 games into a simple structure for the LLM.
        """
        if not games:
            return None

        total_games = len(games)
        wins = 0
        top3 = 0
        total_kills = 0
        most_used_chars = {}

        for game in games:
            if game['gameRank'] == 1:
                wins += 1
            if game['gameRank'] <= 3:
                top3 += 1
            total_kills += game['playerKill']
            
            char_num = game['characterNum']
            most_used_chars[char_num] = most_used_chars.get(char_num, 0) + 1

        # Sort chars by usage
        sorted_chars = sorted(most_used_chars.items(), key=lambda x: x[1], reverse=True)
        top_char = sorted_chars[0][0] if sorted_chars else "Unknown"

        return {
            "total_games": total_games,
            "win_rate": round((wins / total_games) * 100, 1),
            "top3_rate": round((top3 / total_games) * 100, 1),
            "avg_kills": round(total_kills / total_games, 1),
            "top_char_id": top_char # Ideally we'd map this ID to a Name using static data
        }

if __name__ == "__main__":
    # Test
    # You need to set an API Key to test this:
    # os.environ["ER_API_KEY"] = "YOUR_KEY"
    api = EternalReturnAPI()
    
    # Mock lookup if no key
    if not api.api_key:
        print("Please set ER_API_KEY to test.")
    else:
        # Example Test
        uid = api.get_user_id("Hideonbush") # Example name
        if uid:
            print(f"User ID: {uid}")
            stats = api.get_user_stats(uid)
            print("Stats:", stats)
