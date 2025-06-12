chrome.runtime.onInstalled.addListener(() => {
    console.log("[background.js] Extension installed");
  
    chrome.contextMenus.create({
      id: "sendToNotion",
      title: "Send selection to Notion",
      contexts: ["selection"],
    });
  });
  
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log("[background.js] Message received:", message);
  
    if (message.type === "SEND_SELECTED_TEXT") {
      const { text, destination } = message;
      console.log("[background.js] Sending to backend:", { text, destination });
  
      fetch("https://your-backend.duckdns.org/api/capture", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, destination }),
      })
        .then((res) => res.json())
        .then((data) => {
          console.log("[background.js] Response:", data);
        })
        .catch((err) => {
          console.error("[background.js] Error:", err);
        });
    }
  });
  
  // Context menu click handler
  chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "sendToNotion" && info.selectionText) {
      chrome.runtime.sendMessage({
        type: "SEND_SELECTED_TEXT",
        text: info.selectionText,
        destination: "notion",
      });
    }
  });
  