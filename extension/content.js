console.log("[content.js] Content script loaded");

let lastSelectedText = "";
let floatingDiv = null;
let feedbackDiv = null;
let notionConnected = false; // Initialize to false, will be updated by background script

async function checkNotionConnection() {
  try {
    console.log("[content.js] Requesting Notion connection status from background script...");
    const response = await chrome.runtime.sendMessage({ type: "CHECK_NOTION_CONNECTION" });
    notionConnected = response.notionConnected;
    console.log("[content.js] Notion connection status received from background script:", notionConnected);
  } catch (err) {
    notionConnected = false;
    console.error("[content.js] Error requesting Notion connection status from background script:", err);
  }
}

// Call it once on load to get initial status
checkNotionConnection();

function removeFloatingUI() {
  if (floatingDiv) {
    floatingDiv.style.opacity = 0;
    setTimeout(() => {
      floatingDiv?.remove();
      floatingDiv = null;
    }, 300);
  }
  if (feedbackDiv) {
    feedbackDiv.remove();
    feedbackDiv = null;
  }
}

function showFloatingUI(text, rect) {
  removeFloatingUI();

  floatingDiv = document.createElement("div");
  floatingDiv.style.position = "absolute";
  floatingDiv.style.top = `${rect.bottom + window.scrollY + 10}px`;
  floatingDiv.style.left = `${rect.left + window.scrollX}px`;
  floatingDiv.style.zIndex = 999999;
  floatingDiv.style.backdropFilter = "blur(12px)";
  floatingDiv.style.background = "rgba(30, 32, 40, 0.85)";
  floatingDiv.style.color = "#E2E8F0";
  floatingDiv.style.border = "1px solid rgba(255, 255, 255, 0.12)";
  floatingDiv.style.borderRadius = "12px";
  floatingDiv.style.padding = "10px 14px";
  floatingDiv.style.display = "flex";
  floatingDiv.style.alignItems = "center";
  floatingDiv.style.gap = "10px";
  floatingDiv.style.fontFamily = "'Segoe UI', 'Roboto', sans-serif";
  floatingDiv.style.boxShadow = "0 6px 24px rgba(0, 0, 0, 0.35)";
  floatingDiv.style.opacity = 0;
  floatingDiv.style.transition = "opacity 0.3s ease";

  // Destination is always Notion now, so dropdown removed.

  // Send button
  const sendBtn = document.createElement("button");
  sendBtn.textContent = "Send to Notion";
  sendBtn.style.border = "none";
  sendBtn.style.background = "#7B61FF";
  sendBtn.style.color = "#F5F6FA";
  sendBtn.style.padding = "8px 16px";
  sendBtn.style.borderRadius = "8px";
  sendBtn.style.cursor = "pointer";
  sendBtn.style.fontWeight = "bold";
  sendBtn.style.transition = "background 0.3s ease, transform 0.2s ease";
  sendBtn.style.boxShadow = "0 4px 12px rgba(123, 97, 255, 0.4)";
  sendBtn.onmouseenter = () => sendBtn.style.transform = "scale(1.05)";
  sendBtn.onmouseleave = () => sendBtn.style.transform = "scale(1.0)";

  sendBtn.addEventListener("click", () => {
    chrome.runtime.sendMessage({
      type: "SEND_SELECTED_TEXT",
      text: text,
      destination: "notion", // Fixed destination
    });

    showFeedback("Noted to Notion!");
    removeFloatingUI();
    window.getSelection().removeAllRanges();
  });

  floatingDiv.appendChild(sendBtn);
  document.body.appendChild(floatingDiv);

  requestAnimationFrame(() => {
    floatingDiv.style.opacity = 1;
  });
}

function showFeedback(msg) {
    const div = document.createElement("div");
    div.textContent = msg;
    div.style.position = "fixed";
    div.style.top = "20px";
    div.style.left = "50%";
    div.style.transform = "translateX(-50%)";
    div.style.background = "#1F2937"; // dark gray
    div.style.color = "#A5F3FC"; // cyan accent
    div.style.padding = "14px 24px";
    div.style.borderRadius = "12px";
    div.style.boxShadow = "0 4px 20px rgba(0, 0, 0, 0.35)";
    div.style.fontSize = "15px";
    div.style.fontWeight = "500";
    div.style.fontFamily = "'Segoe UI', sans-serif";
    div.style.zIndex = 999999;
    div.style.opacity = "0";
    div.style.transition = "opacity 0.4s ease";
  
    document.body.appendChild(div);
  
    requestAnimationFrame(() => {
      div.style.opacity = "1";
    });
  
    setTimeout(() => {
      div.style.opacity = "0";
      setTimeout(() => {
        if (div && div.parentNode) div.remove();
      }, 300);
    }, 2000); // visible for 2 seconds
  }
  
  

// Use mouseup for showing the floating UI
document.addEventListener("mouseup", async () => {
  console.log("[content.js] mouseup event fired.");
  const selection = window.getSelection();
  const text = selection.toString().trim();
  console.log("[content.js] Selected text on mouseup:", text);

  if (!text) {
    removeFloatingUI();
    console.log("[content.js] No text selected, removing UI.");
    return;
  }

  lastSelectedText = text;
  console.log("[content.js] Highlighted:", text);

  // Re-check Notion connection status via background script if not already true
  if (!notionConnected) {
    console.log("[content.js] Notion not connected, re-checking status via background script...");
    await checkNotionConnection(); // This will now use the background script
    if (!notionConnected) {
      removeFloatingUI();
      console.log("[content.js] Notion still not connected after re-check, removing UI.");
      return;
    }
  }

  // Show the floating UI at the selection
  try {
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    console.log("[content.js] Attempting to show floating UI.");
    showFloatingUI(text, rect);
  } catch (e) {
    // No valid range
    removeFloatingUI();
    console.error("[content.js] Error getting selection range or showing UI:", e);
  }
});

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "GET_HIGHLIGHTED_TEXT") {
    sendResponse({ text: lastSelectedText });
  } else if (msg.type === "UPDATE_NOTION_CONNECTION_STATUS") {
    notionConnected = msg.notionConnected;
    // console.log("[content.js] Notion connection status updated by popup:", notionConnected);
  }
});
