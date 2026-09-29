// Toolbar icon opens the side panel. If the browser has no side panel support (possible in Comet),
// fall back to a narrow popup window docked on the right.
chrome.runtime.onInstalled.addListener(() => {
  if (chrome.sidePanel?.setPanelBehavior) chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => {});
});
chrome.action.onClicked.addListener(async (tab) => {
  try { if (!chrome.sidePanel?.open) throw 0; await chrome.sidePanel.open({ windowId: tab.windowId }); }
  catch (e) {
    const w = await chrome.windows.getCurrent();
    chrome.windows.create({ url: 'panel.html', type: 'popup', width: 380, height: w.height || 900,
      left: (w.left || 0) + (w.width || 1400) - 380, top: w.top || 0 });
  }
});
