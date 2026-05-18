from .base_tool import BaseTool, ToolResult
import os
import platform
import subprocess
import webbrowser
import datetime
from datetime import date
import re
import urllib.parse

class SystemTool(BaseTool):
    name = "system"
    description = "Control the operating system (open apps, volume, search, time, weather, lock)."
    schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string", 
                "enum": ["open_app", "web_search", "weather", "play_music", "get_time", "get_date", "volume_up", "volume_down", "mute", "open_url", "take_screenshot", "calculator", "lock"]
            },
            "app": {"type": "string"},
            "query": {"type": "string"},
            "url": {"type": "string"},
            "value": {"type": "integer"},
            "platform": {"type": "string"}
        },
        "required": ["action"]
    }

    def _play_music(self, query: str, platform: str = "youtube") -> str:
        import urllib.parse, re, httpx

        query = query.strip() if query else "top hits 2026"

        if platform == "spotify":
            url = f"https://open.spotify.com/search/{urllib.parse.quote(query)}"
            webbrowser.open(url)
            return f"Opening Spotify for '{query}'."

        if platform in ("gaana", "jiosaavn"):
            base = "https://gaana.com/search/" if platform == "gaana" \
                   else "https://www.jiosaavn.com/search/"
            webbrowser.open(base + urllib.parse.quote(query))
            return f"Opening {platform} for '{query}'."

        # Default: YouTube — find ACTUAL video URL
        video_url = self._get_youtube_video_url(query)
        if video_url:
            webbrowser.open(video_url)
            return f"Playing '{query}' on YouTube."

        # Fallback: YouTube search
        fallback = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(fallback)
        return f"Opened YouTube search for '{query}'. Click to play."

    def _get_youtube_video_url(self, query: str) -> str | None:
        import httpx, re, urllib.parse
        from loguru import logger
        try:
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9"
            }
            encoded = urllib.parse.quote(query)
            r = httpx.get(
                f"https://www.youtube.com/results?search_query={encoded}",
                headers=headers, timeout=10, follow_redirects=True
            )
            ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', r.text)
            seen, unique = set(), []
            for vid in ids:
                if vid not in seen:
                    seen.add(vid)
                    unique.append(vid)
            if unique:
                return f"https://www.youtube.com/watch?v={unique[0]}&autoplay=1"
        except Exception as e:
            logger.warning(f"YouTube URL fetch failed: {e}")
        return None

    def run(self, action: str, app: str = None, query: str = None, url: str = None, value: int = 10, **kwargs) -> ToolResult:
        sys_os = platform.system()
        
        try:
            if action == "open_app" and app:
                if sys_os == "Windows":
                    os.system(f"start {app}")
                elif sys_os == "Darwin":
                    os.system(f"open -a '{app}'")
                else:
                    subprocess.Popen([app])
                return ToolResult(success=True, output=f"Opened {app}")
                
            elif action == "web_search" and query:
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return ToolResult(success=True, output=f"Searching for {query}")
                
            elif action == "weather":
                import httpx
                city = query or "Hyderabad"
                headers = {"User-Agent": "curl/7.81.0"}
                
                try:
                    # Try 1: wttr.in
                    res = httpx.get(f"https://wttr.in/{city}?format=3", headers=headers, timeout=5.0)
                    if res.status_code == 200 and "error" not in res.text.lower():
                        return ToolResult(success=True, output=res.text.strip())
                    
                    # Try 2: Open-Meteo fallback (no API key needed)
                    # We first need coordinates for the city (using a simple mock for Hyderabad)
                    lat, lon = (17.3850, 78.4867) # Hyderabad
                    if city.lower() != "hyderabad":
                        # Fallback to search if not Hyderabad
                        webbrowser.open(f"https://www.google.com/search?q=weather+in+{city}")
                        return ToolResult(success=True, output=f"I couldn't fetch live data for {city}, so I opened the weather in your browser.")
                        
                    meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                    m_res = httpx.get(meteo_url, timeout=5.0)
                    if m_res.status_code == 200:
                        data = m_res.json()["current_weather"]
                        temp = data["temperature"]
                        wind = data["windspeed"]
                        return ToolResult(success=True, output=f"Hyderabad: {temp}°C, Wind: {wind} km/h")
                        
                except Exception as e:
                    logger.error(f"Weather tool error: {e}")
                
                webbrowser.open(f"https://www.google.com/search?q=weather+in+{city}")
                return ToolResult(success=True, output="wttr.in is down, so I opened the weather in your browser.")
                
            elif action == "play_music" and query:
                plat = kwargs.get("platform", "youtube")
                out_msg = self._play_music(query, plat)
                return ToolResult(success=True, output=out_msg)
                
            elif action == "get_time":
                now = datetime.datetime.now().strftime("It's %I:%M %p")
                return ToolResult(success=True, output=now)
                
            elif action == "get_date":
                today = date.today().strftime("%A, %B %d %Y")
                return ToolResult(success=True, output=today)
                
            elif action == "open_url" and url:
                import re, urllib.parse
                if not url.startswith("http"):
                    url = "https://" + url

                # Convert YouTube search URL to direct video
                if "youtube.com/results" in url:
                    m = re.search(r'search_query=([^&]+)', url)
                    if m:
                        query = urllib.parse.unquote_plus(m.group(1))
                        video = self._get_youtube_video_url(query)
                        if video:
                            webbrowser.open(video)
                            return ToolResult(success=True, output=f"Playing on YouTube.")

                webbrowser.open(url)
                return ToolResult(success=True, output=f"Opened {url}")
                
            elif action == "calculator":
                if sys_os == "Windows":
                    os.system("calc")
                elif sys_os == "Darwin":
                    os.system("open -a Calculator")
                else:
                    os.system("gnome-calculator")
                return ToolResult(success=True, output="Opened calculator")
                
            elif action == "take_screenshot":
                try:
                    import pyautogui
                    filename = f"screenshot_{int(datetime.datetime.now().timestamp())}.png"
                    home = os.path.expanduser("~")
                    filepath = os.path.join(home, filename)
                    pyautogui.screenshot(filepath)
                    return ToolResult(success=True, output=f"Saved screenshot to {filepath}")
                except ImportError:
                    return ToolResult(success=False, output=None, error="pyautogui not installed")
                    
            elif action == "lock":
                if sys_os == "Windows":
                    os.system("rundll32.exe user32.dll,LockWorkStation")
                elif sys_os == "Darwin":
                    os.system("CGSession -suspend")
                else:
                    os.system("gnome-screensaver-command -l")
                return ToolResult(success=True, output="Screen locked")
                
            elif action in ["volume_up", "volume_down", "mute"]:
                if sys_os == "Darwin":
                    if action == "mute":
                        os.system("osascript -e 'set volume output muted true'")
                    else:
                        vol = "up" if action == "volume_up" else "down"
                        os.system(f"osascript -e 'set volume output volume (output volume of (get volume settings) {('+' if vol=='up' else '-')} {value})'")
                elif sys_os == "Linux":
                    if action == "mute":
                        os.system("amixer toggle")
                    else:
                        vol = "+" if action == "volume_up" else "-"
                        os.system(f"amixer set Master {value}%{vol}")
                return ToolResult(success=True, output=f"Executed {action}")
                
            return ToolResult(success=False, output=None, error=f"Unknown system action: {action}")
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))
