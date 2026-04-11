export async function getProvidedApiKey() {
  const url = "https://llmstudy.peach.codes/openaiapikey";

  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to fetch provided API key");
    }

    const data = await response.json();
    return data.apiKey;
  } catch (error) {
    console.error("Error fetching provided API key:", error);
    return null;
  }
}
