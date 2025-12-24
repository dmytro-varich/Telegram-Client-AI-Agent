def load_prompt(file_path: str) -> str:
    """Load prompt text from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        prompt = f.read()
    return prompt