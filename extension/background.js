const BACKEND_URL = "http://localhost:8000/sync-token";
const API_KEY = "static-extension-key";
// In a real app, agent_id would be configured by the user in the extension options.
const AGENT_ID_CLAUDE = "claude-agent-uuid-placeholder";

async function syncToken(provider, token, agentId) {
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
  // Claude Example
  chrome.cookies.get({ url: "https://claude.ai", name: "sessionKey" }, (cookie) => {
    if (cookie) {
      console.log("Found Claude cookie!");
      syncToken("claude", cookie.value, AGENT_ID_CLAUDE);
    }
  });

  // Gemini and OpenAI can be added similarly based on their specific cookie names
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
