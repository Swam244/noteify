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

  const settingsToggleBtn = document.getElementById("settingsToggleBtn");
  const settingsView = document.getElementById("settingsView");
  const backBtn = document.getElementById("backBtn");
  const userInfo = document.getElementById("userInfo");
  const preferenceRadios = document.querySelectorAll('input[name="preference"]');
  const categoryInput = document.getElementById("categoryInput");
  const saveCategoryBtn = document.getElementById("saveCategoryBtn");
  const mainHeader = document.getElementById("mainHeader");
  const destinationOptions = document.getElementById("destinationOptions");
  const statusMsgSettings = document.getElementById("statusMsgSettings");

  let currentUser = null; // Variable to store user data

  // Function to save only preference
  async function savePreference() {
    const selectedPreferenceRadio = document.querySelector('input[name="preference"]:checked');
    const preference = selectedPreferenceRadio ? selectedPreferenceRadio.value : '';

    const dataToSend = { preference };

    statusMsgSettings.textContent = "Saving preference...";
    console.log("savePreference: Setting statusMsgSettings to", statusMsgSettings.textContent);

    try {
      const res = await fetch("https://noteify.duckdns.org/users/preference", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(dataToSend)
      });

      if (res.ok) {
        statusMsgSettings.textContent = "Preference saved successfully!";
        console.log("savePreference: StatusMsgSettings updated to", statusMsgSettings.textContent);
        await checkLoginStatus(); // Re-fetch user status to ensure UI reflects latest state
      } else {
        const errorData = await res.json();
        statusMsgSettings.textContent = `Failed to save preference: ${errorData.message || res.statusText}`;
        console.log("savePreference: StatusMsgSettings updated to error", statusMsgSettings.textContent);
      }
    } catch (err) {
      console.error("[popup.js] Save preference error:", err);
      statusMsgSettings.textContent = "Network error during preference save.";
    }
  }

  // Function to save only category
  async function saveCategory() {
    const category = categoryInput.value.trim();

    if (!category) {
      statusMsgSettings.textContent = "Category cannot be empty.";
      return;
    }

    statusMsgSettings.textContent = "Adding category...";
    console.log("saveCategory: Setting statusMsgSettings to", statusMsgSettings.textContent);

    try {
      // Assuming a POST endpoint for adding new categories
      const res = await fetch("https://noteify.duckdns.org/notes/create/category", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ category })
      });

      if (res.ok) {
        statusMsgSettings.textContent = "Category added successfully!";
        console.log("saveCategory: StatusMsgSettings updated to", statusMsgSettings.textContent);
        categoryInput.value = ''; // Clear input after successful add
        await checkLoginStatus(); // Re-fetch user status to update UI
      } else if (res.status === 409) {
        statusMsgSettings.textContent = "Category already exists.";
        console.log("saveCategory: StatusMsgSettings updated to conflict", statusMsgSettings.textContent);
      } else if (res.status === 500) {
        statusMsgSettings.textContent = "Server error: Failed to add category. Please try again.";
        console.log("saveCategory: StatusMsgSettings updated to server error", statusMsgSettings.textContent);
      } else {
        const errorData = await res.json();
        statusMsgSettings.textContent = `Failed to add category: ${errorData.message || res.statusText}`;
        console.log("saveCategory: StatusMsgSettings updated to generic error", statusMsgSettings.textContent);
      }
    } catch (err) {
      console.error("[popup.js] Add category error:", err);
      statusMsgSettings.textContent = "Network error during category add.";
    }
  }

  // Toggle to settings view
  settingsToggleBtn.addEventListener("click", () => {
    document.querySelectorAll("#loginForm, #highlightedText, #sendBtn, #logoutBtn, #refreshBtn, #settingsToggleBtn, #notionMsg, #notionConnectContainer, #mainHeader, #destinationOptions").forEach(el => {
      el.style.display = "none";
    });
    statusMsg.style.display = "none";
    settingsView.style.display = "flex";
    userInfo.textContent = `${currentUser?.username} (${currentUser?.email})`;

    const validPreferences = ['RAW', 'CATEGORIZED_AND_ENRICHED', 'CATEGORIZED_AND_RAW'];
    if (currentUser?.preference && validPreferences.includes(currentUser.preference)) {
      for (const radio of preferenceRadios) {
        if (radio.value === currentUser.preference) {
          radio.checked = true;
          break;
        }
      }
    } else {
      for (const radio of preferenceRadios) {
        if (radio.value === 'RAW') {
          radio.checked = true;
          break;
        }
      }
    }
    if (currentUser?.category) {
      categoryInput.value = currentUser.category;
    }
  });

  // Back to main view
  backBtn.addEventListener("click", async () => {
    document.querySelectorAll("#loginForm, #highlightedText, #sendBtn, #logoutBtn, #refreshBtn, #settingsToggleBtn, #notionMsg, #notionConnectContainer, #mainHeader, #destinationOptions").forEach(el => {
      el.style.display = "";
    });
    settingsView.style.display = "none";
    statusMsgSettings.textContent = '';
    await checkLoginStatus();
  });

  // Add event listeners to preference radios
  preferenceRadios.forEach(radio => {
    radio.addEventListener('change', savePreference);
  });

  // Save preference and category
  saveCategoryBtn.addEventListener("click", saveCategory);

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs.length) return;
    const tab = tabs[0];
    console.log("[popup.js] Current tab URL:", tab.url);
    // Allow https, http, and file protocols
    if (!/^https?:|^file:/.test(tab.url)) {
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
        textArea.value = response?.text || "";
      }
    );
  });

  async function checkLoginStatus() {
    const isCurrentlyInSettingsView = settingsView.style.display === "flex";
    console.log("checkLoginStatus called. isCurrentlyInSettingsView:", isCurrentlyInSettingsView);

    // Ensure main statusMsg is hidden if in settings view, or cleared if not.
    if (isCurrentlyInSettingsView) {
      statusMsg.style.display = "none";
      statusMsg.textContent = ""; // Clear main status msg content
      console.log("checkLoginStatus: Main statusMsg hidden (in settings view).");
    } else {
      statusMsg.textContent = ""; // Clear main status msg content
      statusMsg.style.display = "none"; // Default to hidden, will be shown if needed later
      console.log("checkLoginStatus: Main statusMsg cleared and hidden (not in settings view).");
    }

    try {
      const res = await fetch("https://noteify.duckdns.org/users/login", {
        method: "GET",
        credentials: "include"
      });
      console.log("checkLoginStatus fetch response status:", res.status);

      if (res.status === 200) {
        const data = await res.json();
        currentUser = data;
        console.log("Current User Data:", currentUser);
        userInfo.textContent = `${data.username} (${data.email})`;

        if (isCurrentlyInSettingsView) {
          console.log("checkLoginStatus: Keeping settings view active.");
          statusMsg.style.display = "none";
          statusMsg.textContent = ""; // Ensure it's clear as well
          console.log("checkLoginStatus: Main statusMsg explicitly hidden and cleared within settings block.");
          logoutBtn.style.display = "none";
          loginForm.style.display = "none";
          notionConnectContainer.style.display = "none";
          textArea.style.display = "none";
          sendBtn.style.display = "none";
          notionMsg.style.display = "none";
          settingsToggleBtn.style.display = "none";
          destinationOptions.style.display = "none";
          mainHeader.style.display = "none";
        } else {
          console.log("checkLoginStatus: Setting up main view.");
          loginForm.style.display = "none";
          logoutBtn.style.display = "block";

          if (!data.notionConnected) {
            notionMsg.textContent = "Please connect your Notion account.";
            notionMsg.style.display = "block";
            notionConnectContainer.style.display = "flex";
            textArea.style.display = "none";
            sendBtn.style.display = "none";
            statusMsg.style.display = "none";
            settingsToggleBtn.style.display = "none";
            destinationOptions.style.display = "none";
            mainHeader.style.display = "block"; // Show main header
          } else {
            notionMsg.style.display = "none";
            notionConnectContainer.style.display = "none";
            textArea.style.display = "block";
            sendBtn.style.display = "block";
            statusMsg.style.display = "block";
            settingsToggleBtn.style.display = "block";
            destinationOptions.style.display = "block";
            mainHeader.style.display = "block"; // Show main header
          }
        }

        // Update Notion connection status in content script regardless of view
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs.length && /^https?:/.test(tabs[0].url)) {
            chrome.tabs.sendMessage(tabs[0].id, { type: "UPDATE_NOTION_CONNECTION_STATUS", notionConnected: data.notionConnected });
          }
        });

      } else if (res.status === 401) {
        // If not logged in, always revert to login screen and hide settings view
        loginForm.style.display = "block";
        logoutBtn.style.display = "none";
        notionConnectContainer.style.display = "none";
        textArea.style.display = "none";
        sendBtn.style.display = "none";
        notionMsg.style.display = "none";
        settingsToggleBtn.style.display = "none";
        destinationOptions.style.display = "none";
        settingsView.style.display = "none"; // Crucial: ensure settings view is hidden if not logged in
        mainHeader.style.display = "block"; // Ensure header is shown on login page
      } else {
        console.log("checkLoginStatus: Unexpected error.");
        if (!isCurrentlyInSettingsView) {
          statusMsg.textContent = "Unexpected error. Try again later.";
          statusMsg.style.display = "block";
          console.log("checkLoginStatus: Main statusMsg showing for unexpected error.", statusMsg.textContent);
        }
      }
    } catch (err) {
      console.error("[popup.js] Network error in checkLoginStatus:", err);
      if (!isCurrentlyInSettingsView) {
        statusMsg.textContent = "Network error. Check server.";
        statusMsg.style.display = "block";
        console.log("checkLoginStatus: Main statusMsg showing for network error.", statusMsg.textContent);
      }
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
      window.open("https://noteify.duckdns.org/oauth2/notion", "_blank");
    });
  }

  if (refreshBtn) {
    refreshBtn.addEventListener("click", () => {
      window.location.reload();
    });
  }

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
          currentUser = null;
          await checkLoginStatus();
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
      const res = await fetch("https://noteify.duckdns.org/notes/create", {
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
