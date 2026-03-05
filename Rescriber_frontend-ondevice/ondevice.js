export async function getOnDeviceResponseDetect(userMessage, onResultCallback) {
  const response = await fetch("https://localhost:5331/detect", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message: userMessage }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n").filter((line) => line.trim() !== "");
    for (const line of lines) {
      try {
        const jsonObject = JSON.parse(line);
        if (jsonObject.results) {
          await onResultCallback(jsonObject.results);
        }
      } catch (e) {
        console.error("Error parsing JSON:", e);
      }
    }

    // 清空 buffer
    buffer = "";
  }
}

export async function getOnDeviceResponseCluster(userMessageCluster) {
  const response = await fetch("https://localhost:5331/cluster", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message: userMessageCluster }),
  });
  const data = await response.json();
  const resultString = data.results;
  return data.results;
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
  const response = await fetch("https://localhost:5331/abstract", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message: userMessage }),
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Process each line of the response
    const lines = buffer.split("\n").filter((line) => line.trim() !== "");
    for (const line of lines) {
      try {
        const jsonObject = JSON.parse(line);
        if (jsonObject.results) {
          // Call the callback with the current results
          await onResultCallback(jsonObject.results);
        }
      } catch (e) {
        console.error("Error parsing JSON chunk:", e);
      }
    }

    buffer = "";
  }
}
