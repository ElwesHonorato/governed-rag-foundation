const button = document.getElementById("send");
const promptEl = document.getElementById("prompt");
const resultEl = document.getElementById("result");
const citationsEl = document.getElementById("citations");
const messages = [];

function renderTranscript() {
  if (messages.length === 0) {
    resultEl.textContent = "Response will appear here.";
    return;
  }
  resultEl.textContent = messages
    .map((m) => `${m.role.toUpperCase()}: ${m.content}`)
    .join("\n\n");
}

async function sendPrompt() {
  const prompt = promptEl.value.trim();
  if (!prompt) {
    resultEl.textContent = "Write a prompt first.";
    return;
  }

  messages.push({ role: "user", content: prompt });
  promptEl.value = "";
  resultEl.textContent = "Sending...";

  try {
    const res = await fetch("/prompt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });

    const data = await res.json();
    if (!res.ok) {
      messages.pop();
      resultEl.textContent = data.error || "Request failed.";
      return;
    }

    if (data.assistant_message && typeof data.assistant_message.content === "string") {
      messages.push(data.assistant_message);
    } else if (typeof data.response === "string") {
      messages.push({ role: "assistant", content: data.response });
    }

    if (Array.isArray(data.citations) && data.citations.length > 0) {
      citationsEl.textContent = data.citations
        .map((citation, idx) => {
          const source = citation.source_key || "unknown-source";
          const quote = citation.quote || "";
          return `${idx + 1}. ${source}\n"${quote}"`;
        })
        .join("\n\n");
    } else {
      citationsEl.textContent = "No citations returned.";
    }
    renderTranscript();
  } catch (err) {
    messages.pop();
    resultEl.textContent = "Network error. Please try again.";
  }
}

button.addEventListener("click", sendPrompt);
