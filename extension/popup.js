document.addEventListener("DOMContentLoaded", () => {
    const textArea = document.getElementById("highlightedText");
    const sendBtn = document.getElementById("sendBtn");
    const statusMsg = document.getElementById("statusMsg");
  
    console.log("[popup.js] Popup loaded.");
  
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs.length) {
        console.error("[popup.js] No active tab.");
        return;
      }
  
      chrome.tabs.sendMessage(
        tabs[0].id,
        { type: "GET_HIGHLIGHTED_TEXT" },
        (response) => {
          if (chrome.runtime.lastError) {
            console.error("[popup.js] Error:", chrome.runtime.lastError.message);
            textArea.placeholder = "Failed to get text";
            return;
          }
          console.log("[popup.js] Received response:", response);
          textArea.value = response?.text || "";
        }
      );
    });
  
    sendBtn.addEventListener("click", async () => {
      const text = textArea.value.trim();
      const destination = document.querySelector('input[name="destination"]:checked').value;
  
      if (!text) {
        statusMsg.textContent = "No text to send.";
        return;
      }
  
      statusMsg.textContent = "Sending...";
  
      try {
        const res = await fetch("https://your-backend.duckdns.org/api/capture", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text, destination })
        });
  
        const data = await res.json();
        if (res.ok) {
          statusMsg.textContent = "Sent successfully!";
        } else {
          statusMsg.textContent = "API Error: " + (data?.message || "Failed to send.");
        }
      } catch (err) {
        console.error("[popup.js] Fetch error:", err);
        statusMsg.textContent = "Network error. Check HTTPS or CORS.";
      }
    });
  });
  