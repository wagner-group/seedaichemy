def prompt_generation(prompt):
    return [{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": prompt}]

def save_prompt(location: str, content:str) -> None:
    """Saves the prompt to a filelocation."""
    with open(location, 'w+') as prompt_file:
      prompt_file.write(content)