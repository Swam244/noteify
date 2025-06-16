console.log("[content.js] Content script loaded");


function isValidPDFUrl(url) {
  if (!url) return false;
  if (!url.toLowerCase().endsWith('.pdf')) return false;
  if (url.startsWith('file:')) return false;
  if (url.includes('viewer.html') || url.includes('pdfproxy')) return false;
  return true;
}

function injectButton(container, pdfUrl, index) {
  if (!isValidPDFUrl(pdfUrl)) return;
  if (container.querySelector(`.noteify-btn-${index}`)) return;

  const btn = document.createElement('button');
  btn.innerText = '📄 Open using Noteify';
  btn.className = `noteify-btn-${index}`;
  btn.style.position = 'absolute';
  btn.style.top = `${10 + index * 40}px`;
  btn.style.right = '10px';
  btn.style.zIndex = '9999';
  btn.style.backgroundColor = '#007bff';
  btn.style.color = '#fff';
  btn.style.padding = '6px 10px';
  btn.style.border = 'none';
  btn.style.borderRadius = '4px';
  btn.style.cursor = 'pointer';

  const proxiedUrl = `https://noteify.duckdns.org/pdfproxy?url=${encodeURIComponent(pdfUrl)}`;
  const viewerUrl = `https://noteify.duckdns.org/pdfjs/web/viewer.html?file=${encodeURIComponent(proxiedUrl)}`;

  btn.onclick = () => window.open(viewerUrl, '_blank');

  const style = getComputedStyle(container);
  if (style.position === 'static') container.style.position = 'relative';
  container.appendChild(btn);
  console.log(`✅ Injected Noteify button for ${pdfUrl}`);
}

let lastDetectedPDFs = new Set();

function detectAllPDFs() {
  const seen = new Set();
  let index = 0;

  const candidates = [
    ...document.querySelectorAll('iframe, embed, object'),
    ...Array.from(document.querySelectorAll('a')).filter(a => a.href.endsWith('.pdf'))
  ];

  console.log(`[Noteify] Found ${candidates.length} candidates`);

  for (const el of candidates) {
    let url = el.src || el.data || el.getAttribute('src') || el.getAttribute('data');
    if (!url) continue;

    if (url.includes('blob:')) continue; // Skip non-remote blobs

    if (url.includes('.pdf') || el.type === 'application/pdf') {
      if (seen.has(url)) continue;
      seen.add(url);
      injectButton(el.parentElement || el, url, index++);
    }
  }

  console.log(`[Noteify] Injected buttons for ${seen.size} unique PDFs`);
  lastDetectedPDFs = seen;
}

document.addEventListener('DOMContentLoaded', () => {
  setTimeout(() => detectAllPDFs(), 1000); // Delay to allow iframes to render

  let debounceTimer = null;
  const observer = new MutationObserver(() => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      console.log('[Noteify] Mutation observed, re-scanning...');
      detectAllPDFs();
    }, 500); // Debounced re-scan after mutations
  });

  observer.observe(document.body, { childList: true, subtree: true });
});







function redirectToViewer(pdfUrl) {
  if (
    pdfUrl.startsWith('file://') ||                   // Don't redirect local PDFs
    pdfUrl.includes('pdfproxy') || 
    pdfUrl.includes('viewer.html') || 
    !pdfUrl.endsWith('.pdf')
  ) return;

  const proxiedUrl = `https://noteify.duckdns.org/pdfproxy?url=${encodeURIComponent(pdfUrl)}`;
  const viewerUrl = `https://noteify.duckdns.org/pdfjs/web/viewer.html?file=${encodeURIComponent(proxiedUrl)}`;
  window.location.href = viewerUrl;
}

if (
  window.location.href.endsWith('.pdf') &&
  !window.location.href.includes('/viewer.html') &&
  !window.location.href.startsWith('file://')
) {
  redirectToViewer(window.location.href);
}




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
  floatingDiv.style.backdropFilter = "blur(8px)";
  floatingDiv.style.background = "rgba(45, 55, 72, 0.95)";
  floatingDiv.style.color = "#A5F3FC";
  floatingDiv.style.border = "1px solid rgba(255, 255, 255, 0.08)";
  floatingDiv.style.borderRadius = "8px";
  floatingDiv.style.padding = "8px 12px";
  floatingDiv.style.display = "flex";
  floatingDiv.style.alignItems = "center";
  floatingDiv.style.gap = "8px";
  floatingDiv.style.fontFamily = "'Segoe UI', 'Roboto', sans-serif";
  floatingDiv.style.boxShadow = "0 4px 16px rgba(0, 0, 0, 0.25)";
  floatingDiv.style.opacity = 0;
  floatingDiv.style.transition = "opacity 0.2s ease";
  floatingDiv.style.transform = "scale(0.95)";
  floatingDiv.style.transformOrigin = "top left";

  // Send button
  const sendBtn = document.createElement("button");
  sendBtn.textContent = "Note to Notion";
  sendBtn.style.border = "none";
  sendBtn.style.background = "#4A5568";
  sendBtn.style.color = "#A5F3FC";
  sendBtn.style.padding = "6px 12px";
  sendBtn.style.borderRadius = "6px";
  sendBtn.style.cursor = "pointer";
  sendBtn.style.fontWeight = "500";
  sendBtn.style.fontSize = "13px";
  sendBtn.style.transition = "background 0.2s ease, transform 0.2s ease";
  sendBtn.style.boxShadow = "0 2px 8px rgba(0, 0, 0, 0.2)";
  sendBtn.onmouseenter = () => {
    sendBtn.style.background = "#2D3748";
    sendBtn.style.transform = "scale(1.02)";
  };
  sendBtn.onmouseleave = () => {
    sendBtn.style.background = "#4A5568";
    sendBtn.style.transform = "scale(1.0)";
  };

  sendBtn.addEventListener("click", async () => {
    chrome.runtime.sendMessage({
      type: "SEND_SELECTED_TEXT",
      text: text,
      destination: window.location.href,
    }, async (response) => {
      console.log("[content.js] Received response from background:", response);
      
      // Handle error responses
      if (response && response.status === 400) {
        console.log("[content.js] Received 400 error:", response.detail);
        showFeedback(response.detail || "Invalid text length. Please select text between 30 and 2000 characters.");
        removeFloatingUI();
        window.getSelection().removeAllRanges();
        return;
      }

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
            destination: window.location.href
          }, (confirmResponse) => {
            console.log("[content.js] Received confirmResponse:", confirmResponse);
            if (confirmResponse && confirmResponse.message) {
              showFeedback(confirmResponse.message);
            } else {
              showFeedback("Failed to send to Notion after confirmation. Please try again.");
            }
          });
        } else {
          showFeedback("Category confirmation cancelled.");
        }
      } else if (response && response.hasOwnProperty('message')) {
        console.log("[content.js] Response contains message property:", response.message);
        // Show general message for RAW preference or other backend messages
        showFeedback(response.message || "Sent successfully!");
      } else if (response) {
        console.log("[content.js] Generic success response (no category/message property, but response is not null/undefined).");
        showFeedback("Sent successfully!");
      } else {
        console.log("[content.js] Response is unexpected or empty (null/undefined/false).");
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
    floatingDiv.style.transform = "scale(1)";
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
  
async function showCategoryConfirmationForm(category, text) {
  // Fetch available categories through background script
  let availableCategories = [];
  try {
    const response = await chrome.runtime.sendMessage({ type: "GET_CATEGORIES" });
    console.log("[content.js] Received categories from background:", response);
    availableCategories = response.categories || [];
  } catch (error) {
    console.error("[content.js] Failed to fetch categories:", error);
  }

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

  if (availableCategories.length > 0) {
    const categoriesHeading = document.createElement("p");
    categoriesHeading.textContent = "Existing Note Pages:";
    categoriesHeading.style.margin = "0 0 10px 0";
    categoriesHeading.style.color = "#fff";
    formDiv.appendChild(categoriesHeading);

    const categoriesContainer = document.createElement("div");
    categoriesContainer.style.display = "flex";
    categoriesContainer.style.flexWrap = "wrap";
    categoriesContainer.style.gap = "8px";
    categoriesContainer.style.marginBottom = "15px";

    availableCategories.forEach(cat => {
      const categoryChip = document.createElement("button");
      categoryChip.textContent = cat;
      categoryChip.style.padding = "4px 8px";
      categoryChip.style.background = "#4A5568";
      categoryChip.style.color = "#fff";
      categoryChip.style.border = "none";
      categoryChip.style.borderRadius = "4px";
      categoryChip.style.cursor = "pointer";
      categoryChip.style.fontSize = "12px";
      categoryChip.onclick = () => {
        categoryInput.value = cat;
      };
      categoriesContainer.appendChild(categoryChip);
    });

    formDiv.appendChild(categoriesContainer);
  }

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
