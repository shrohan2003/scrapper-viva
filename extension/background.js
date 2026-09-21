// The bridge only connects to the Python server on this computer.
const BRIDGE = "http://127.0.0.1:8765";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const pageUrl = sender.url || sender.tab?.url || "";

  // Accept messages only from EVENTIM pages.
  if (!/^https:\/\/(www\.)?eventim\.de\//.test(pageUrl)) {
    sendResponse({ error: "Message did not come from EVENTIM" });
    return false;
  }

  if (message.type === "CHECK_CAPTURE") {
    fetch(`${BRIDGE}/status`)
      .then((response) => response.json())
      .then(sendResponse)
      .catch(() => sendResponse({ capture: false }));

    // The fetch finishes asynchronously, so keep the message channel open.
    return true;
  }

  if (message.type === "SEND_CAPTURE") {
    fetch(`${BRIDGE}/capture`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: pageUrl,
        html: message.html
      })
    })
      .then(async (response) => ({
        ok: response.ok,
        ...(await response.json())
      }))
      .then(sendResponse)
      .catch((error) =>
        sendResponse({ ok: false, error: String(error) })
      );

    return true;
  }

  return false;
});
