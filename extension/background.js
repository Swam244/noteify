chrome.runtime.onInstalled.addListener(() => {
    console.log("[background.js] Extension installed");
  
    chrome.contextMenus.create({
      id: "sendToNotion",
      title: "Send selection to Notion",
      contexts: ["selection"],
    });
  });
  
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    // console.log("[background.js] Message received:", message);
  
    if (message.type === "SEND_SELECTED_TEXT") {
        const { text, destination, checked } = message;
      // console.log("[background.js] Sending to backend:", { text, destination });
  
      // Get user data which includes preference
      fetch("https://noteify.duckdns.org/users/login", {
        method: "GET",
        credentials: "include"
      })
      .then(res => res.json())
      .then(userData => {
        const preference = userData.preference || 'RAW';
        // console.log("[background.js] User preference:", preference);
        
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
          body: JSON.stringify({ text, destination, ...(typeof checked !== 'undefined' ? { checked } : {}) }),
        });
      })
      .then(res => {
        // console.log("[background.js] Fetch response status for SEND_SELECTED_TEXT:", res.status);
        return res.json().then(data => ({ status: res.status, ...data }));
      })
      .then(data => {
        // console.log("[background.js] Parsed data for SEND_SELECTED_TEXT:", data);
        // Ensure a message is always sent back
        if (!data.message && !data.category && !data.detail) {
          data.message = "Sent successfully!"; // Default success message
        }
        // If the response contains a token, pass it along to the content script
        if (data.token) {
          sendResponse({ ...data, token: data.token });
        } else {
        sendResponse(data);
        }
      })
      .catch((err) => {
        console.error("[background.js] Error sending selected text:", err);
        sendResponse({ message: "Failed to send to Notion. Please try again." });
      });
      return true; // Indicates that sendResponse will be called asynchronously
    } else if (message.type === "CHECK_NOTION_CONNECTION") {
      // console.log("[background.js] Checking Notion connection status...");
      fetch("https://noteify.duckdns.org/users/login", {
        method: "GET",
        credentials: "include"
      })
      .then(res => res.json())
      .then(data => {
        const notionConnectedStatus = !!data.notionConnected;
        // console.log("[background.js] Notion connection status fetched:", notionConnectedStatus);
        sendResponse({ notionConnected: notionConnectedStatus });
      })
      .catch(err => {
        console.error("[background.js] Error checking Notion connection:", err);
        sendResponse({ notionConnected: false });
      });
      return true; // Indicates that sendResponse will be called asynchronously
    } else if (message.type === "CONFIRM_CATEGORY") {
      const { text, category, destination, enrichment, checked, token } = message;
      // console.log("[background.js] Confirming category:", { text, category, destination, enrichment });

      // Get user preference first
      fetch("https://noteify.duckdns.org/users/login", {
        method: "GET",
        credentials: "include"
      })
      .then(res => res.json())
      .then(userData => {
        const preference = userData.preference;
        // console.log("[background.js] User preference for confirmation:", preference);
        
        // Choose endpoint based on preference and enrichment
        let endpoint;
        if (preference === 'CATEGORIZED_AND_ENRICHED' && enrichment) {
          endpoint = "https://noteify.duckdns.org/notes/create/enriched";
        } else {
          endpoint = "https://noteify.duckdns.org/notes/create";
        }

        // Send the data to appropriate endpoint, including token if present
        return fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
          body: JSON.stringify({ 
            text, 
            category, 
            destination,
            ...(enrichment && { enrichment }),
            ...(typeof checked !== 'undefined' ? { checked } : {}),
            ...(token ? { token } : {})
          }),
        });
      })
      .then(res => {
        // console.log("[background.js] Fetch response status for CONFIRM_CATEGORY:", res.status);
        return res.json().then(data => ({ status: res.status, ...data }));
      })
      .then(data => {
        // console.log("[background.js] Parsed data for CONFIRM_CATEGORY:", data);
        // Ensure a message is always sent back
        if (!data.message && !data.category && !data.detail) {
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
      // console.log("[background.js] Fetching categories...");
      fetch("https://noteify.duckdns.org/notes/categories", {
        method: "GET",
        credentials: "include"
      })
      .then(res => res.json())
      .then(data => {
        // console.log("[background.js] Categories fetched:", data);
        sendResponse(data);
      })
      .catch(err => {
        console.error("[background.js] Error fetching categories:", err);
        sendResponse({ categories: [] });
      });
      return true; // Indicates that sendResponse will be called asynchronously
    } else if (message.type === "GET_USER_PREFERENCE") {
      // console.log("[background.js] Getting user preference...");
      fetch("https://noteify.duckdns.org/users/login", {
        method: "GET",
        credentials: "include"
      })
      .then(res => res.json())
      .then(data => {
        // console.log("[background.js] User preference fetched:", data.preference);
        sendResponse({ preference: data.preference });
      })
      .catch(err => {
        console.error("[background.js] Error fetching user preference:", err);
        sendResponse({ preference: 'RAW' });
      });
      return true; // Indicates that sendResponse will be called asynchronously
    } else if (message.type === 'SELECTION_DONE') {
      // console.log("[background.js] Received SELECTION_DONE message:", message);
      fetch('https://noteify.duckdns.org/users/getuploadtoken', { credentials: 'include' })
        .then(res => res.json())
        .then(tokenData => {
          const uploadToken = tokenData.token || '';
          // Try to get the tabId from sender or fallback to active tab
          let tabId = sender.tab && sender.tab.id;
          if (!tabId) {
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
              if (tabs.length > 0) {
                tabId = tabs[0].id;
                sendCropMessage(tabId, message, uploadToken);
              } else {
                console.error('[background.js] Could not determine tabId for screenshot upload.');
              }
            });
          } else {
            sendCropMessage(tabId, message, uploadToken);
          }
        });
    } else if (message.type === "UPLOAD_SCREENSHOT") {
      const { image, category } = message;
      // console.log("[background.js] Uploading screenshot (with category):", category);

      function dataURLtoBlob(dataurl) {
        var arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1],
          bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n);
        while(n--){
          u8arr[n] = bstr.charCodeAt(n);
        }
        return new Blob([u8arr], {type:mime});
      }

      const blob = dataURLtoBlob(image);
      const formData = new FormData();
      formData.append("file", blob, "screenshot.png");
      if (category) {
        formData.append("category", category);
      }

      fetch("https://noteify.duckdns.org/notes/create/image", {
        method: "POST",
        body: formData,
        credentials: "include"
      })
      .then(async res => {
        if (res.status === 401) {
          sendResponse({ status: 401 });
          return;
        }
        const data = await res.json();
        sendResponse({ success: true, data });
      })
      .catch(err => {
        console.error("[background.js] Screenshot upload failed:", err);
        sendResponse({ success: false });
      });
      return true; // async
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
  
  function sendCropMessage(tabId, message, uploadToken) {
    // console.log('[background.js] Sending uploadToken to tab:', tabId, 'token:', uploadToken);
    chrome.tabs.captureVisibleTab(null, { format: "png" }, (dataUrl) => {
      chrome.tabs.sendMessage(tabId, {
        type: 'CROP_AND_UPLOAD',
        dataUrl,
        coords: message.coords,
        uploadToken
      });
    });
  }
  