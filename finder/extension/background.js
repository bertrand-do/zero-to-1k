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

// Watched accounts: every 30s ask the finder what's new and pop a browser notification. Click = open the post.
const WAPI = 'http://127.0.0.1:5191/api/items?tab=watched';
chrome.alarms.create('watch', { periodInMinutes: 0.5 });
chrome.runtime.onStartup.addListener(() => chrome.alarms.create('watch', { periodInMinutes: 0.5 }));
chrome.alarms.onAlarm.addListener(async (a) => {
  if (a.name !== 'watch') return;
  let d; try { d = await (await fetch(WAPI)).json(); } catch (e) { return; }   // finder not running
  const { wseen } = await chrome.storage.local.get('wseen');
  const first = !wseen, seen = new Set(wseen || []);
  for (const i of d.items || []) {
    if (seen.has(i.id)) continue;
    seen.add(i.id);
    if (first || i.age > 30) continue;   // first run only records what's already out
    chrome.notifications.create('w|' + i.url, {
      type: 'basic', iconUrl: 'icons/128.png', priority: 2, requireInteraction: true,
      title: `@${i.handle} just posted`, message: (i.text || '').slice(0, 180), contextMessage: 'Click to open it and reply now',
    });
  }
  chrome.storage.local.set({ wseen: [...seen].slice(-2000) });
});
chrome.notifications.onClicked.addListener(async (id) => {
  if (!id.startsWith('w|')) return;
  const url = id.slice(2), win = await chrome.windows.getLastFocused({ windowTypes: ['normal'] }).catch(() => null);
  chrome.tabs.create(win ? { url, windowId: win.id } : { url });
  if (win) chrome.windows.update(win.id, { focused: true });
  chrome.notifications.clear(id);
});
