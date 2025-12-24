def format_context(chunks):
    return "\n\n".join([chunk["content"] for chunk in chunks])