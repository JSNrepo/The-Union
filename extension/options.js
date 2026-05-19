document.addEventListener('DOMContentLoaded', () => {
  // Load saved options
  chrome.storage.local.get(['claudeAgentId', 'geminiAgentId', 'openaiAgentId', 'apiKey'], (items) => {
    document.getElementById('claudeAgentId').value = items.claudeAgentId || '';
    document.getElementById('geminiAgentId').value = items.geminiAgentId || '';
    document.getElementById('openaiAgentId').value = items.openaiAgentId || '';
    document.getElementById('apiKey').value = items.apiKey || '';
  });

  // Save options
  document.getElementById('saveButton').addEventListener('click', () => {
    const claudeAgentId = document.getElementById('claudeAgentId').value;
    const geminiAgentId = document.getElementById('geminiAgentId').value;
    const openaiAgentId = document.getElementById('openaiAgentId').value;
    const apiKey = document.getElementById('apiKey').value;

    chrome.storage.local.set({
      claudeAgentId: claudeAgentId,
      geminiAgentId: geminiAgentId,
      openaiAgentId: openaiAgentId,
      apiKey: apiKey
    }, () => {
      const status = document.getElementById('status');
      status.textContent = 'Options saved.';
      setTimeout(() => {
        status.textContent = '';
      }, 2000);
    });
  });
});