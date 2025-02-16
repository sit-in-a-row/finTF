const { spawn } = require("child_process");
const express = require("express");
const cors = require("cors");
const OpenAI = require("openai");
const yaml = require("yamljs");
const path = require("path");
const fetch = require("node-fetch"); // node-fetch 패키지 설치 필요

const app = express();
const PORT = 1234;  // 포트 번호 1234 사용

// YAML 파일에서 API 키 로드
const configPath = path.resolve(__dirname, "../config/api_keys.yaml");
const config = yaml.load(configPath);
const openAiApiKey = config["api_keys"]["open_ai"];
const notionToken = config["api_keys"]["NOTION_API_TOKEN"];

// OpenAI API 설정
const openai = new OpenAI({
    apiKey: openAiApiKey
});

// Notion API 요청에 사용할 헤더
const HEADERS = {
    "Authorization": `Bearer ${notionToken}`,
    "Notion-Version": "2022-06-28",  // Notion API 버전 (필요에 따라 조정)
    "Content-Type": "application/json"
};

// CORS 설정 (모든 도메인 허용 및 Preflight 요청 허용)
app.use(cors({
    origin: "*",
    methods: ["GET", "POST", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"]
}));

app.options("*", (req, res) => {
    res.header("Access-Control-Allow-Origin", "*");
    res.header("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.header("Access-Control-Allow-Headers", "Content-Type, Authorization");
    res.sendStatus(200);
});

app.use(express.json());

// 정적 파일 제공
app.use(express.static(__dirname));
app.use('/pipeline', express.static(path.join(__dirname, '../pipeline')));

// 기본 페이지 (index.html) 렌더링
app.get("/", (req, res) => {
    res.sendFile(path.join(__dirname, "index.html"));
});

// OpenAI API 호출 엔드포인트
app.post("/gpt", async (req, res) => {
    try {
        const { system, prompt } = req.body;
        const response = await openai.chat.completions.create({
            model: "gpt-4o-mini",
            messages: [
                { role: "system", content: system },
                { role: "user", content: prompt }
            ],
            max_tokens: 3000,
            temperature: 0.7
        });
        res.header("Access-Control-Allow-Origin", "*");
        res.json(response);
    } catch (error) {
        console.error("Error calling OpenAI API:", error);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

// /get_raw_info 엔드포인트: Python 스크립트를 실행하여 데이터를 가져옴
app.post("/get_raw_info", (req, res) => {
    const { user_input } = req.body;
    const pythonProcess = spawn("python3", ["./get_raw_info_for_chatbot.py", user_input]);
    let dataToSend = "";
    
    pythonProcess.stdout.on("data", (data) => {
        const output = data.toString();
        console.log(output);
        dataToSend += output;
    });

    pythonProcess.stderr.on("data", (data) => {
        console.error("Python 에러:", data.toString());
    });

    pythonProcess.on("close", (code) => {
        console.log(`Python 프로세스 종료, 코드: ${code}`);
        res.header("Access-Control-Allow-Origin", "*");
        res.json({ result: dataToSend });
    });
});

/**
 * /get_page_text 엔드포인트:
 * 쿼리 스트링으로 전달된 pageId를 바탕으로 Notion API에서 해당 페이지의 블록들을 가져와
 * 텍스트만 추출한 후, 최종 텍스트를 콘솔과 JSON 응답으로 출력합니다.
 */
app.get("/get_page_text", async (req, res) => {
    try {
        const pageId = req.query.pageId;
        if (!pageId) {
            return res.status(400).json({ error: "Missing pageId" });
        }
        const url = `https://api.notion.com/v1/blocks/${pageId}/children`;
        const response = await fetch(url, { headers: HEADERS });
        if (!response.ok) {
            const errorData = await response.json();
            console.log(`Error: ${response.status}`, errorData);
            return res.status(response.status).json(errorData);
        }
        const data = await response.json();
        const blocks = data.results || [];
        let texts = [];
        blocks.forEach(block => {
            if (block.type === "paragraph") {
                const paragraph = block.paragraph || {};
                const rich_texts = paragraph.rich_text || [];
                rich_texts.forEach(rt => {
                    if (rt.text && rt.text.content) {
                        texts.push(rt.text.content);
                    }
                });
            }
        });
        const finalText = texts.join("");
        console.log("노션 페이지 텍스트:", finalText);
        res.json({ text: finalText });
    } catch (err) {
        console.error("Error fetching page text:", err);
        res.status(500).json({ error: err.toString() });
    }
});

// 서버 실행
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
});
