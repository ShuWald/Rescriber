const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");
const { default: ollama } = require("ollama");
const https = require("https");
const fs = require("fs");
require("dotenv").config();

const app = express();
const httpPort = 3000;
const httpsPort = 5331; // 3443
app.use(cors());
app.use(bodyParser.json());

const models = {
  detect: {
    modelName: "detectModel",
    prompt: `You are an expert in cybersecurity and data privacy. You are now tasked to detect PII from the given text, using the following taxonomy only:
      ADDRESS
      IP_ADDRESS
      URL
      SSN
      PHONE_NUMBER
      EMAIL
      DRIVERS_LICENSE
      PASSPORT_NUMBER
      TAXPAYER IDENTIFICATION NUMBER
      ID_NUMBER
      NAME
      USERNAME
      KEYS: Passwords, passkeys, API keys, encryption keys, and any other form of security keys.
      GEOLOCATION: Places and locations, such as cities, provinces, countries, international regions, or named infrastructures (bus stops, bridges, etc.).
      AFFILIATION: Names of organizations, such as public and private companies, schools, universities, public institutions, prisons, healthcare institutions, non-governmental organizations, churches, etc.
      DEMOGRAPHIC_ATTRIBUTE: Demographic attributes of a person, such as native language, descent, heritage, ethnicity, nationality, religious or political group, birthmarks, ages, sexual orientation, gender and sex.
      TIME: Description of a specific date, time, or duration.
      HEALTH_INFORMATION: Details concerning an individual's health status, medical conditions, treatment records, and health insurance information.
      FINANCIAL_INFORMATION: Financial details such as bank account numbers, credit card numbers, investment records, salary information, and other financial statuses or activities.
      EDUCATIONAL_RECORD: Educational background details, including academic records, transcripts, degrees, and certification.
      For the given message that a user sends to a chatbot, identify all the personally identifiable information using the above taxonomy only, and the entity_type should be selected from the all-caps categories.
      Note that the information should be related to a real person not in a public context, but okay if not uniquely identifiable.
      Result should be in its minimum possible unit.
      Return me ONLY a json object in the following format (no other extra text!): {"results": [{"entity_type": YOU_DECIDE_THE_PII_TYPE, "text": PART_OF_MESSAGE_YOU_IDENTIFIED_AS_PII]}`,
  },
  cluster: {
    modelName: "clusterModel",
    prompt: `For the given message, find ALL segments of the message with the same contextual meaning as the given PII. Consider segments that are semantically related or could be inferred from the original PII or share a similar context or meaning. List all of them in a list, and each segment should only appear once in each list.  Please return only in JSON format. Each PII provided will be a key, and its value would be the list PIIs (include itself) that has the same contextual meaning.

    Example 1:
    Input:
    <message>I will be the valedictorian of my class. Please write me a presentation based on the following information: As a student at Vanderbilt University, I feel honored. The educational journey at Vandy has been nothing less than enlightening. The dedicated professors here at Vanderbilt are the best. As an 18 year old student at VU, the opportunities are endless.</message>
    <pii1>Vanderbilt University</pii1>
    <pii2>18 year old</pii2>
    <pii3>VU</pii3>
    Expected JSON output:
    {'Vanderbilt University': ['Vanderbilt University', 'Vandy', 'VU', 'Vanderbilt'], '18 year old':['18 year old'], 'VU':[ 'VU', 'Vanderbilt University', 'Vandy', 'Vanderbilt']}
    
    Example 2:
    Input:
    <message>Do you know Bill Gates and the company he founded, Microsoft? Can you send me an article about how he founded it to my email at jeremyKwon@gmail.com please?</message>
    <pii1>Bill Gates</pii1>
    <pii2>jeremyKwon@gmail.com</pii2>
    Expected JSON output:
    {'Bill Gates': ['Bill Gates', 'Microsoft'], 'jeremyKwon@gmail.com':['jeremyKwon@gmail.com']}`,
  },
  abstract: {
    modelName: "abstractModel",
    prompt: `Rewrite the text to abstract the protected information, and don't change other parts. Please return with JSON format. 
    For example if the input is:
    <Text>I graduated from CMU, and I earn a six-figure salary now. Today in the office, I had some conflict with my boss, and I am thinking about whether I should start interviewing with other companies to get a better offer.</Text>
    <ProtectedInformation>CMU, Today</ProtectedInformation>
    Then the output JSON format should be: {"results": YOUR_REWRITE} where YOUR_REWRITE needs to be a string that no longer contains ProtectedInformation, here's a sample YOUR_REWRITE: I graduated from a prestigious university, and I earn a six-figure salary now. Recently in the office, I had some conflict with my boss, and I am thinking about whether I should start interviewing with other companies to get a better offer.`,
  },
};

async function pullModel(modelName) {
  try {
    await ollama.pull({ model: modelName });
    console.log(`Model '${modelName}' has been pulled successfully.`);
  } catch (error) {
    console.error(`Failed to pull the model: ${error.message}`);
  }
}

async function createModel(modelKey) {
  const { modelName, prompt } = models[modelKey];
  const modelfile = `
    FROM llama3.2
    SYSTEM "${prompt}"
  `;
  try {
    await ollama.create({ model: modelName, modelfile: modelfile });
    console.log(`Model '${modelName}' has been created successfully.`);
  } catch (error) {
    console.error(`Failed to create the model: ${error.message}`);
  }
}

app.post("/detect", async (req, res) => {
  const userMessage = req.body.message;

  try {
    console.log("Waiting for DETECT response...");
    const maxSegmentLength = 500;
    let segments = [];

    for (let i = 0; i < userMessage.length; i += maxSegmentLength) {
      segments.push(userMessage.substring(i, i + maxSegmentLength));
    }

    const mergedResponse = { results: [] };

    for (let i = 0; i < segments.length; ++i) {
      const segment = segments[i];
      try {
        const response = await ollama.chat({
          model: models.detect.modelName,
          messages: [{ role: "user", content: segment }],
          format: "json",
          options: { temperature: 0 },
        });

        const jsonObject = JSON.parse(response.message.content);

        if (jsonObject.results && Array.isArray(jsonObject.results)) {
          mergedResponse.results.push(...jsonObject.results);
        }
      } catch (error) {
        console.error(`Error parsing JSON from segment: ${segment}`, error);
      }
    }

    // Deduplicate results based on "text"
    const uniqueResults = new Map();
    mergedResponse.results.forEach((item) => {
      if (!uniqueResults.has(item.text)) {
        uniqueResults.set(item.text, item);
      }
    });

    mergedResponse.results = Array.from(uniqueResults.values());

    res.send(mergedResponse); // Ensure the response matches Python server format
    console.log("DETECT response sent.", mergedResponse);
  } catch (error) {
    console.error("Error running Ollama:", error);
    res
      .status(500)
      .send({ error: "Error running Ollama", details: error.message });
  }
});

app.post("/cluster", async (req, res) => {
  const userMessage = req.body.message;

  try {
    console.log("Waiting for CLUSTER response...");
    const response = await ollama.chat({
      model: models.cluster.modelName,
      messages: [{ role: "user", content: userMessage }],
      format: "json",
    });

    res.send({ results: response.message.content });
    console.log("CLUSTER response sent.");
  } catch (error) {
    console.error("Error running Ollama:", error);
    res
      .status(500)
      .send({ error: "Error running Ollama", details: error.message });
  }
});

app.post("/abstract", async (req, res) => {
  const userMessage = req.body.message;

  try {
    console.log("Waiting for ABSTRACT response...");
    const response = await ollama.chat({
      model: models.abstract.modelName,
      messages: [{ role: "user", content: userMessage }],
      format: "json",
    });

    const jsonObject = JSON.parse(response.message.content);
    if (jsonObject.results) {
      res.send({ results: jsonObject.results }); // Ensure consistent format
    } else {
      res.send({ results: "Unable to abstract the content" });
    }

    console.log("ABSTRACT response sent.");
  } catch (error) {
    console.error("Error running Ollama:", error);
    res
      .status(500)
      .send({ error: "Error running Ollama", details: error.message });
  }
});

app.get("/openaiapikey", async (req, res) => {
  const apiKey = process.env.OPENAI_API_KEY;
  if (apiKey) {
    res.status(200).json({ apiKey });
  } else {
    res.status(500).json({ error: "API key not found" });
  }
});

const httpsOptions = {
  key: fs.readFileSync("selfsigned.key"),
  cert: fs.readFileSync("selfsigned.crt"),
};

https.createServer(httpsOptions, app).listen(httpsPort, () => {
  // console.log(`HTTPS Server running at https://34.23.212.219:${httpsPort}`);
  console.log(`HTTPS Server running at https://localhost:${httpsPort}`);
});

app.listen(httpPort, "0.0.0.0", () => {
  console.log(`HTTP Server running at http://localhost:${httpPort}`);
});

app.get("/", async (req, res) => {
  console.log("Get request received!");
  res.send("HI");
});

pullModel("llama3.2").then(async () => {
  await createModel("detect");
  // await createModel("cluster");
  await createModel("abstract");
});
