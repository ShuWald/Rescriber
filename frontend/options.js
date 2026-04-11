document.getElementById("saveButton").addEventListener("click", () => {
  const apiOption = document.querySelector(
    'input[name="apiOption"]:checked'
  ).value;
  const apiKey = document.getElementById("apiKey").value;

  chrome.storage.sync.set({ apiOption, openaiApiKey: apiKey }, () => {
    alert("Settings saved.");
  });
});

chrome.storage.sync.get(["apiOption", "openaiApiKey"], (result) => {
  if (result.apiOption) {
    document.querySelector(
      `input[name="apiOption"][value="${result.apiOption}"]`
    ).checked = true;
  }
  if (result.apiOption === "own" && result.openaiApiKey) {
    document.getElementById("apiKey").value = result.openaiApiKey;
  }
});

// Disable or enable the API key input based on the selected option
document.querySelectorAll('input[name="apiOption"]').forEach((radio) => {
  radio.addEventListener("change", () => {
    document.getElementById("apiKey").disabled = radio.value !== "own";
  });
});
