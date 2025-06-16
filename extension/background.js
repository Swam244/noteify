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
  
      // Get user data which includes preference
      fetch("https://noteify.duckdns.org/users/login", {
        method: "GET",
        credentials: "include"
      })
      .then(res => res.json())
      .then(userData => {
        const preference = userData.preference || 'RAW';
        console.log("[background.js] User preference:", preference);
        
        // Choose endpoint based on preference
        let endpoint;
        if (preference === 'RAW') {
          endpoint = "https://noteify.duckdns.org/notes/create/raw";
        } else if (preference === 'CATEGORIZED_AND_ENRICHED') {
          endpoint = "https://noteify.duckdns.org/notes/category";
        } else if (preference === 'CATEGORIZED_AND_RAW') {
          endpoint = "https://noteify.duckdns.org/notes/category";
        }

        // Send the text to appropriate endpoint
        return fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({ text, destination }),
        });
      })
      .then(res => {
        console.log("[background.js] Fetch response status for SEND_SELECTED_TEXT:", res.status);
        return res.json().then(data => ({ status: res.status, ...data }));
      })
      .then(data => {
        console.log("[background.js] Parsed data for SEND_SELECTED_TEXT:", data);
        // Ensure a message is always sent back
        if (!data.message && !data.category && !data.detail) {
          data.message = "Sent successfully!"; // Default success message
        }
        sendResponse(data);
      })
      .catch((err) => {
        console.error("[background.js] Error sending selected text:", err);
        sendResponse({ message: "Failed to send to Notion. Please try again." });
      });
      return true; // Indicates that sendResponse will be called asynchronously
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
    } else if (message.type === "CONFIRM_CATEGORY") {
      const { text, category, destination } = message;
      console.log("[background.js] Confirming category:", { text, category, destination });

      fetch("https://noteify.duckdns.org/notes/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ text, category, destination }),
      })
      .then(res => {
        console.log("[background.js] Fetch response status for CONFIRM_CATEGORY:", res.status);
        return res.json();
      })
      .then(data => {
        console.log("[background.js] Parsed data for CONFIRM_CATEGORY:", data);
        // Ensure a message is always sent back
        if (!data.message && !data.category) {
          data.message = "Category confirmed successfully!"; // Default success message
        }
        sendResponse(data);
      })
      .catch(err => {
        console.error("[background.js] Error confirming category:", err);
        sendResponse({ message: "Failed to confirm category. Please try again." });
      });
      return true; // Indicates that sendResponse will be called asynchronously
    } else if (message.type === "GET_CATEGORIES") {
      console.log("[background.js] Fetching categories...");
      fetch("https://noteify.duckdns.org/notes/categories", {
        method: "GET",
        credentials: "include"
      })
      .then(res => res.json())
      .then(data => {
        console.log("[background.js] Categories fetched:", data);
        sendResponse(data);
      })
      .catch(err => {
        console.error("[background.js] Error fetching categories:", err);
        sendResponse({ categories: [] });
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
        destination: tab.url,
      });
    }
  });
  