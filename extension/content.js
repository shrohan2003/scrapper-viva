// Run on EVENTIM pages and wait for the seating blocks to appear.
const BLOCKS = 'g.block-outlines path.bo[id^="bo"]';
let busy = false;

function checkForCapture() {
  if (busy || !location.pathname.startsWith("/event/")) return;
  if (document.querySelectorAll(BLOCKS).length === 0) return;

  busy = true;

  // Ask Python whether the user has pressed Enter yet.
  chrome.runtime.sendMessage({ type: "CHECK_CAPTURE" }, (status) => {
    if (chrome.runtime.lastError || !status?.capture) {
      busy = false;
      return;
    }

    // Do not send data from a different EVENTIM tab.
    if (!location.pathname.includes(status.event_id)) {
      busy = false;
      return;
    }

    // Send the rendered DOM directly to Python; do not save raw HTML.
    chrome.runtime.sendMessage(
      {
        type: "SEND_CAPTURE",
        html: document.documentElement.outerHTML
      },
      (reply) => {
        busy = false;
        if (chrome.runtime.lastError || !reply?.ok) {
          console.warn("Scrapper Viva capture was not accepted", reply);
        }
      }
    );
  });
}

// The check is small; the full HTML is sent only after Enter is pressed.
setInterval(checkForCapture, 1000);