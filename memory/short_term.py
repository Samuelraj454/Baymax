from collections import deque
from typing import List, Dict

class ShortTermMemory:
    def __init__(self, max_turns: int = 20):
        # 20 turns = 40 messages total (user + assistant pairs)
        self.max_turns = max_turns
        self.memory = deque(maxlen=max_turns * 2)

    def add(self, role: str, content: str):
        self.memory.append({"role": role, "content": content})

    def get(self) -> List[Dict[str, str]]:
        return list(self.memory)

    def clear(self):
        self.memory.clear()

    def __len__(self) -> int:
        return len(self.memory)
