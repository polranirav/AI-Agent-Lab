# Stage 1 — Core LLM Agent with Tool Use

> **"Research + Calculator CLI Agent"** — A single-agent system that demonstrates LLM function calling, tool orchestration, and the foundational perceive → think → act → observe loop.

---

## 🎯 What This Stage Covers

- LLM fundamentals: tokens, context windows, temperature, message roles
- Structured outputs & JSON schemas
- Tool / function calling with a dynamic tool registry
- The single-agent loop: **perceive → think → act → observe → answer**

## 🛠️ Mini-Project

A CLI agent with 2–3 tools (search, calculator, date/time) that:
- Takes a natural language question
- Decides which tool(s) to invoke
- Chains operations to produce a final answer

## 📂 Structure

```
stage-1-core-agent-with-tools/
├── README.md          ← You are here
├── agent/             ← Core agent logic
├── tools/             ← Tool registry & implementations
├── config/            ← Prompts, schemas, settings
└── examples/          ← Sample runs & outputs
```

## 🧪 Example Prompt

> "What's 25% of the total price of a MacBook Air ($1,199) and iPhone 15 ($799)?"

The agent should chain: add prices → calculate percentage → return result.

---

*Part of the [AI Agent Lab](https://github.com/polranirav/AI-Agent-Lab) learning path.*
