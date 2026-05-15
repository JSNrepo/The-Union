document.addEventListener('DOMContentLoaded', () => {
  // Load saved options
  chrome.storage.local.get(['claudeAgentId', 'geminiAgentId', 'openaiAgentId'], (items) => {
    document.getElementById('claudeAgentId').value = items.claudeAgentId || '';
    document.getElementById('geminiAgentId').value = items.geminiAgentId || '';
    document.getElementById('openaiAgentId').value = items.openaiAgentId || '';
  });

  // Save options
  document.getElementById('saveButton').addEventListener('click', () => {
    const claudeAgentId = document.getElementById('claudeAgentId').value;
    const geminiAgentId = document.getElementById('geminiAgentId').value;
    const openaiAgentId = document.getElementById('openaiAgentId').value;

    chrome.storage.local.set({
      claudeAgentId: claudeAgentId,
      geminiAgentId: geminiAgentId,
      openaiAgentId: openaiAgentId
    }, () => {
      const status = document.getElementById('status');
      status.textContent = 'Options saved.';
      setTimeout(() => {
        status.textContent = '';
      }, 2000);
    });
  });
});