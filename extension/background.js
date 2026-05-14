const BACKEND_URL = "http://localhost:8000/sync-token";
const API_KEY = "static-extension-key";

async function syncToken(provider, token, agentId) {
  if (!agentId) return;
  try {
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
      },
      body: JSON.stringify({
        provider: provider,
        token: token,
        agent_id: agentId
      })
    });
    console.log(`Synced ${provider} token:`, await response.json());
  } catch (error) {
    console.error(`Failed to sync ${provider} token:`, error);
  }
}

async function checkCookies() {
  chrome.storage.local.get(['claudeAgentId', 'geminiAgentId', 'openaiAgentId'], (items) => {
    // Claude Example
    if (items.claudeAgentId) {
      chrome.cookies.get({ url: "https://claude.ai", name: "sessionKey" }, (cookie) => {
        if (cookie) {
          console.log("Found Claude cookie!");
          syncToken("claude", cookie.value, items.claudeAgentId);
        }
      });
    }

    // Gemini
    if (items.geminiAgentId) {
      chrome.cookies.get({ url: "https://gemini.google.com", name: "__Secure-1PSID" }, (cookie) => {
        if (cookie) {
          console.log("Found Gemini cookie!");
          syncToken("gemini", cookie.value, items.geminiAgentId);
        }
      });
    }

    // OpenAI
    if (items.openaiAgentId) {
      chrome.cookies.get({ url: "https://chatgpt.com", name: "__Secure-next-auth.session-token" }, (cookie) => {
        if (cookie) {
          console.log("Found OpenAI cookie!");
          syncToken("openai", cookie.value, items.openaiAgentId);
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
