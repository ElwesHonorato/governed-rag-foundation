const button = document.getElementById("send");
const promptEl = document.getElementById("prompt");
const resultEl = document.getElementById("result");

async function sendPrompt() {
  const prompt = promptEl.value.trim();
  if (!prompt) {
    resultEl.textContent = "Write a prompt first.";
    return;
  }

  resultEl.textContent = "Sending...";

  try {
    const res = await fetch("/prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    const data = await res.json();
    if (!res.ok) {
      resultEl.textContent = data.error || "Request failed.";
      return;
    }

    resultEl.textContent = [
      `Prompt: ${data.prompt}`,
      `Model: ${data.model}`,
      `Response: ${data.response}`,
    ].join("\n");
  } catch (err) {
    resultEl.textContent = "Network error. Please try again.";
  }
}

button.addEventListener("click", sendPrompt);
