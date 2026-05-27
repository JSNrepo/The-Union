const BACKEND_URL = "http://localhost:8000/sync-token";

async function syncToken(provider, token, agentId, apiKey) {
  if (!agentId || !apiKey) return;
  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey
      },
      body: JSON.stringify({
        provider: provider,
        token: token,
        agent_id: agentId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    console.log(`Synced ${provider} token:`, await response.json());
  } catch (error) {
    console.error(`Failed to sync ${provider} token:`, error);
  }
}

async function checkCookies() {
  chrome.storage.local.get(['claudeAgentId', 'geminiAgentId', 'openaiAgentId', 'apiKey'], (items) => {
    const apiKey = items.apiKey;
    if (!apiKey) {
      console.error("API Key not configured in options.");
      return;
    }

    // Claude Example
    if (items.claudeAgentId) {
      chrome.cookies.get({ url: "https://claude.ai", name: "sessionKey" }, (cookie) => {
        if (cookie) {
          console.log("Found Claude cookie!");
          syncToken("claude", cookie.value, items.claudeAgentId, apiKey);
        }
      });
    }

    // Gemini
    if (items.geminiAgentId) {
      chrome.cookies.get({ url: "https://gemini.google.com", name: "__Secure-1PSID" }, (cookie) => {
        if (cookie) {
          console.log("Found Gemini cookie!");
          syncToken("gemini", cookie.value, items.geminiAgentId, apiKey);
        }
      });
    }

    // OpenAI
    if (items.openaiAgentId) {
      chrome.cookies.get({ url: "https://chatgpt.com", name: "__Secure-next-auth.session-token" }, (cookie) => {
        if (cookie) {
          console.log("Found OpenAI cookie!");
          syncToken("openai", cookie.value, items.openaiAgentId, apiKey);
        }
      });
    }
  });
}

chrome.runtime.onInstalled.addListener(() => {
  console.log("Union Token Bridge installed.");
  chrome.alarms.create("syncCookies", { periodInMinutes: 5 });
  checkCookies();
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "syncCookies") {
    checkCookies();
  }
});
