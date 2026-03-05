// background.js
console.log("Background script running");

// Handle streaming fetch requests (detect, abstract) via long-lived port
chrome.runtime.onConnect.addListener((port) => {
  port.onMessage.addListener(async ({ url, body }) => {
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          port.postMessage({ done: true });
          break;
        }
        port.postMessage({ chunk: decoder.decode(value, { stream: true }) });
      }
    } catch (err) {
      port.postMessage({ error: err.message });
    }
  });
});

// Handle non-streaming fetch requests (cluster) via one-shot message
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "fetch") {
    fetch(request.url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request.body),
    })
      .then((r) => r.json())
      .then((data) => sendResponse({ data }))
      .catch((err) => sendResponse({ error: err.message }));
    return true; // keep channel open for async response
  }
});
