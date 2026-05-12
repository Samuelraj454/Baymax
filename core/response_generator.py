import re

def generate_speak_text(text: str) -> str:
    """
    Clean text for TTS:
    - Strips all markdown
    - Strips all JSON
    - Strips all symbols
    - Truncates to 3 sentences
    - Normalizes spaces
    """
    if not text:
        return ""

    # 1. Remove JSON blocks { ... }
    clean = re.sub(r'\{[^}]*\}', '', text)

    # 2. Remove Markdown symbols: * _ # ` ~ [ ] ( )
    clean = re.sub(r'[*_#`~]', '', clean)
    
    # 3. Remove Special Symbols / Icons
    clean = re.sub(r'[✓✗⏳⚠═─█◆▸]', '', clean)

    # 4. Normalize spaces and newlines
    clean = clean.replace('\n', ' ').strip()
    clean = re.sub(r'\s+', ' ', clean)

    # 5. Split into sentences and take max 3
    # Simple regex for sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', clean)
    clean = " ".join(sentences[:3])

    return clean.strip()
