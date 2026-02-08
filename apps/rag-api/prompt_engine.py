import random

REMIX_TEMPLATES = [
    "Explain this like an over-caffeinated squirrel: {prompt}",
    "Turn this into a pirate motivational speech: {prompt}",
    "Rewrite this as a dramatic soap-opera cliffhanger: {prompt}",
    "Make this sound like a chef yelling in a cooking show: {prompt}",
    "Convert this into a medieval royal decree: {prompt}",
    "Say this as if a robot just discovered stand-up comedy: {prompt}",
]

FUNNY_ENDINGS = [
    "with jazz hands",
    "while riding a unicycle",
    "and then everyone clapped",
    "in pirate mode",
    "but make it legally confusing",
    "in full soap-opera drama",
]


def build_funny_reply(prompt: str) -> dict[str, str]:
    original_prompt = prompt.strip()
    if not original_prompt:
        raise ValueError("prompt is required")

    if len(original_prompt) > 2000:
        raise ValueError("prompt is too long (max 2000 characters)")

    remix = random.choice(REMIX_TEMPLATES).format(prompt=original_prompt)
    response = f"Hello World ({random.choice(FUNNY_ENDINGS)})"
    return {"original": original_prompt, "remix": remix, "response": response}
