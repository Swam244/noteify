document.addEventListener("DOMContentLoaded", () => {
    const textArea = document.getElementById("highlightedText");
    const sendBtn = document.getElementById("sendBtn");
    const statusMsg = document.getElementById("statusMsg");
    const loginForm = document.getElementById("loginForm");
    const loginEmail = document.getElementById("loginEmail");
    const loginPassword = document.getElementById("loginPassword");
    const loginBtn = document.getElementById("loginBtn");
    const notionMsg = document.getElementById("notionMsg");
    const notionConnectContainer = document.getElementById("notionConnectContainer");
    const connectNotionBtn = document.getElementById("connectNotionBtn");
    const refreshBtn = document.getElementById("refreshBtn");
    const logoutBtn = document.getElementById("logoutBtn");
  
    // console.log("[popup.js] Popup loaded.");
  
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs.length) {
        console.error("[popup.js] No active tab.");
        return;
      }
  
      const tab = tabs[0];
      // Only try to send message if the tab is http(s)
      if (!/^https?:/.test(tab.url)) {
        textArea.placeholder = "Not available on this page";
        return;
      }
  
      chrome.tabs.sendMessage(
        tab.id,
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
  
    async function checkLoginStatus() {
      try {
        const res = await fetch("https://noteify.duckdns.org/users/login", {
          method: "GET",
          credentials: "include"
        });
        if (res.status === 200) {
          const data = await res.json();
          console.log('[popup.js] Login response:', data);
          console.log('[popup.js] notion_connected:', data.notionConnected, typeof data.notionConnected);
          // Send update to content script
          chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs.length && /^https?:/.test(tabs[0].url)) {
              console.log("[popup.js] Sending Notion connection status to content script:", data.notionConnected);
              chrome.tabs.sendMessage(tabs[0].id, { type: "UPDATE_NOTION_CONNECTION_STATUS", notionConnected: data.notionConnected });
            }
          });
          // Hide login form
          if (loginForm) loginForm.style.display = "none";
          // Show logout button
          if (logoutBtn) logoutBtn.style.display = "block";
          // Check Notion connection
          if (!data.notionConnected) {
            if (notionMsg) {
              notionMsg.textContent = "Please connect your Notion account.";
              notionMsg.style.display = "block";
            }
            if (notionConnectContainer) notionConnectContainer.style.display = "flex";
            if (textArea) textArea.style.display = "none";
            if (sendBtn) sendBtn.style.display = "none";
            if (statusMsg) statusMsg.style.display = "none";
          } else {
            if (notionMsg) notionMsg.style.display = "none";
            if (notionConnectContainer) notionConnectContainer.style.display = "none";
            if (textArea) textArea.style.display = "block";
            if (sendBtn) sendBtn.style.display = "block";
            if (statusMsg) statusMsg.style.display = "block";
          }
        } else if (res.status === 401) {
          // Not logged in, show login form
          if (loginForm) loginForm.style.display = "block";
          // Hide logout button
          if (logoutBtn) logoutBtn.style.display = "none";
          if (notionConnectContainer) notionConnectContainer.style.display = "none";
          if (textArea) textArea.style.display = "none";
          if (sendBtn) sendBtn.style.display = "none";
          if (notionMsg) notionMsg.style.display = "none";
        } else {
          statusMsg.textContent = "Unexpected error. Try again later.";
        }
      } catch (err) {
        statusMsg.textContent = "Network error. Check server.";
      }
    }
  
    if (loginForm && loginBtn) {
      loginBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        const email = loginEmail.value.trim();
        const password = loginPassword.value.trim();
        if (!email || !password) {
          statusMsg.textContent = "Enter email and password.";
          return;
        }
        statusMsg.textContent = "Signing in...";
        try {
          const res = await fetch("https://noteify.duckdns.org/users/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify({ email, password })
          });
          if (res.status === 200) {
            statusMsg.textContent = "Login successful!";
            await checkLoginStatus();
          } else {
            statusMsg.textContent = "Login failed. Check credentials.";
          }
        } catch (err) {
          statusMsg.textContent = "Network error during login.";
        }
      });
    }
  
    if (connectNotionBtn) {
      connectNotionBtn.addEventListener("click", () => {
        // Open Notion OAuth URL in a new tab
        window.open("https://noteify.duckdns.org/oauth2/notion", "_blank");
      });
    }
  
    if (refreshBtn) {
      refreshBtn.addEventListener("click", () => {
        window.location.reload();
      });
    }
  
    // Logout button logic
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        statusMsg.textContent = "Logging out...";
        try {
          const res = await fetch("https://noteify.duckdns.org/users/logout", {
            method: "POST",
            credentials: "include"
          });
  
          if (res.ok) {
            statusMsg.textContent = "Logged out successfully!";
            await checkLoginStatus(); // Re-check status to update UI
          } else {
            statusMsg.textContent = "Logout failed.";
          }
        } catch (err) {
          console.error("[popup.js] Logout error:", err);
          statusMsg.textContent = "Network error during logout.";
        }
      });
    }
  
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
  
    checkLoginStatus();
  });
  