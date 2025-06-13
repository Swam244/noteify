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
    } else if (message.type === "CHECK_NOTION_CONNECTION") {
      console.log("[background.js] Checking Notion connection status...");
      fetch("https://noteify.duckdns.org/users/login", {
        method: "GET",
        credentials: "include"
      })
      .then(res => res.json())
      .then(data => {
        const notionConnectedStatus = !!data.notionConnected;
        console.log("[background.js] Notion connection status fetched:", notionConnectedStatus);
        sendResponse({ notionConnected: notionConnectedStatus });
      })
      .catch(err => {
        console.error("[background.js] Error checking Notion connection:", err);
        sendResponse({ notionConnected: false });
      });
      return true; // Indicates that sendResponse will be called asynchronously
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
  