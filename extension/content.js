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

  sendBtn.addEventListener("click", async () => {
    chrome.runtime.sendMessage({
      type: "SEND_SELECTED_TEXT",
      text: text,
      destination: "notion", // Fixed destination
    }, async (response) => {
      console.log("[content.js] Received response from background:", response);
      if (response && response.category) {
        console.log("[content.js] Response contains category:", response.category);
        // Show category confirmation form if a category is predicted
        const result = await showCategoryConfirmationForm(response.category, text);
        if (result.confirmed) {
          // Send the confirmed category back to the backend
          chrome.runtime.sendMessage({
            type: "CONFIRM_CATEGORY",
            text: text,
            category: result.category,
            destination: "notion"
          }, (confirmResponse) => {
            if (confirmResponse && confirmResponse.message) {
              showFeedback(confirmResponse.message);
            } else {
              showFeedback("Failed to send to Notion after confirmation. Please try again.");
            }
          });
        }
      } else if (response && response.message) {
        console.log("[content.js] Response contains message:", response.message);
        // Show general message for RAW preference or other backend messages
        showFeedback(response.message);
      } else {
        console.log("[content.js] Response is unexpected or empty.");
        showFeedback("Failed to send to Notion. Please try again.");
      }
      removeFloatingUI();
      window.getSelection().removeAllRanges();
    });
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
  
function showCategoryConfirmationForm(category, text) {
  const formDiv = document.createElement("div");
  formDiv.style.position = "fixed";
  formDiv.style.top = "20px";
  formDiv.style.left = "50%";
  formDiv.style.transform = "translateX(-50%)";
  formDiv.style.background = "#1F2937";
  formDiv.style.color = "#A5F3FC";
  formDiv.style.padding = "20px";
  formDiv.style.borderRadius = "12px";
  formDiv.style.boxShadow = "0 4px 20px rgba(0, 0, 0, 0.35)";
  formDiv.style.fontSize = "15px";
  formDiv.style.fontWeight = "500";
  formDiv.style.fontFamily = "'Segoe UI', sans-serif";
  formDiv.style.zIndex = "999999";
  formDiv.style.width = "300px";

  const heading = document.createElement("h3");
  heading.textContent = "Predicted Category";
  heading.style.margin = "0 0 15px 0";
  heading.style.color = "#fff";
  formDiv.appendChild(heading);

  const subheading = document.createElement("p");
  subheading.textContent = "Do you want to proceed?";
  subheading.style.margin = "0 0 15px 0";
  formDiv.appendChild(subheading);

  const categoryInput = document.createElement("input");
  categoryInput.type = "text";
  categoryInput.value = category;
  categoryInput.style.width = "100%";
  categoryInput.style.padding = "8px";
  categoryInput.style.marginBottom = "15px";
  categoryInput.style.background = "#2D3748";
  categoryInput.style.border = "1px solid #4A5568";
  categoryInput.style.borderRadius = "6px";
  categoryInput.style.color = "#fff";
  formDiv.appendChild(categoryInput);

  const buttonContainer = document.createElement("div");
  buttonContainer.style.display = "flex";
  buttonContainer.style.gap = "10px";
  buttonContainer.style.justifyContent = "flex-end";

  const confirmBtn = document.createElement("button");
  confirmBtn.textContent = "Confirm";
  confirmBtn.style.padding = "8px 16px";
  confirmBtn.style.background = "#7B61FF";
  confirmBtn.style.color = "#fff";
  confirmBtn.style.border = "none";
  confirmBtn.style.borderRadius = "6px";
  confirmBtn.style.cursor = "pointer";

  const cancelBtn = document.createElement("button");
  cancelBtn.textContent = "Cancel";
  cancelBtn.style.padding = "8px 16px";
  cancelBtn.style.background = "#4A5568";
  cancelBtn.style.color = "#fff";
  cancelBtn.style.border = "none";
  cancelBtn.style.borderRadius = "6px";
  cancelBtn.style.cursor = "pointer";

  buttonContainer.appendChild(cancelBtn);
  buttonContainer.appendChild(confirmBtn);
  formDiv.appendChild(buttonContainer);

  document.body.appendChild(formDiv);

  return new Promise((resolve) => {
    confirmBtn.onclick = () => {
      formDiv.remove();
      resolve({ confirmed: true, category: categoryInput.value });
    };

    cancelBtn.onclick = () => {
      formDiv.remove();
      resolve({ confirmed: false });
    };
  });
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
