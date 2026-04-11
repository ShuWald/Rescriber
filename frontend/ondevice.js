function streamViaBackground(url, body, onChunk) {
  return new Promise((resolve, reject) => {
    const port = chrome.runtime.connect({ name: "stream" });
    let buffer = "";

    port.onMessage.addListener(async (msg) => {
      if (msg.error) {
        port.disconnect();
        reject(new Error(msg.error));
        return;
      }
      if (msg.done) {
        port.disconnect();
        resolve();
        return;
      }
      buffer += msg.chunk;
      const lines = buffer.split("\n").filter((l) => l.trim() !== "");
      // keep last incomplete line in buffer
      const lastChar = msg.chunk[msg.chunk.length - 1];
      buffer = lastChar === "\n" ? "" : lines.pop() || "";
      for (const line of lines) {
        try {
          const jsonObject = JSON.parse(line);
          if (jsonObject.results) await onChunk(jsonObject.results);
        } catch (e) {
          console.error("Error parsing JSON:", e);
        }
      }
    });

    port.postMessage({ url, body });
  });
}

export async function getOnDeviceResponseDetect(userMessage, onResultCallback) {
  await streamViaBackground(
    "https://localhost:5331/detect",
    { message: userMessage },
    onResultCallback
  );
}

export async function getOnDeviceResponseCluster(userMessageCluster) {
  const result = await chrome.runtime.sendMessage({
    type: "fetch",
    url: "https://localhost:5331/cluster",
    body: { message: userMessageCluster },
  });
  if (result.error) throw new Error(result.error);
  return result.data.results;
}

export async function getOnDeviceAbstractResponse(
  originalMessage,
  currentMessage,
  abstractList,
  onResultCallback
) {
  const userMessage = `<Text>${currentMessage}</Text>\n<ProtectedInformation>${abstractList.join(
    ", "
  )}</ProtectedInformation>`;
  await streamViaBackground(
    "https://localhost:5331/abstract",
    { message: userMessage },
    onResultCallback
  );
}
