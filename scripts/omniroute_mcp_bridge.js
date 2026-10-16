#!/usr/bin/env node
/**
 * OmniRoute Unified Model Context Protocol (MCP) Bridge for Antigravity & Claude Desktop
 * Exposes the world's leading AI models (Claude Opus, Sonnet, DeepSeek R1, Gemini 2.0, Llama 3.3, Ollama)
 * to reasoning chats with automatic $0-cost routing and fallback.
 */

const http = require('http');
const readline = require('readline');

const OMNIROUTE_URL = process.env.OMNIROUTE_URL || 'http://127.0.0.1:20128';
const OMNIROUTE_TOKEN = process.env.OMNIROUTE_API_KEY || process.env.OMNIROUTE_TOKEN || process.env.OMNIROUTE_LOCAL_TOKEN || 'omniroute-secret-key-local';
const OLLAMA_URL = process.env.OLLAMA_URL || 'http://127.0.0.1:11434';

function httpRequest(urlStr, options, data) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const reqOptions = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + (url.search || ''),
      method: options.method || 'GET',
      headers: options.headers || {}
    };

    const req = http.request(reqOptions, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(body) });
        } catch (e) {
          resolve({ status: res.statusCode, data: body });
        }
      });
    });

    req.on('error', reject);
    if (data) {
      req.write(typeof data === 'string' ? data : JSON.stringify(data));
    }
    req.end();
  });
}

const TOOLS = [
  {
    name: 'ask_claude_opus',
    description: 'Dispatch an architectural, complex reasoning, or deep synthesis problem to Claude Opus via OmniRoute gateway.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'The complex problem, architectural design, or prompt for Claude Opus' },
        system: { type: 'string', description: 'Optional system prompt for context and persona' }
      }
    }
  },
  {
    name: 'ask_claude_sonnet',
    description: 'Dispatch coding, debugging, or precise engineering tasks to Claude 3.7 / 3.5 Sonnet via OmniRoute.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Code implementation, debugging, or engineering instruction' },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_deepseek_r1_reasoning',
    description: 'Execute deep mathematical, logical, and chain-of-thought reasoning using DeepSeek R1 reasoning champion.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Problem requiring deep mathematical, algorithmic, or logical reasoning' },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_gemini_frontier',
    description: 'Query Google Gemini 3.1 Flash Lite via Google AI Studio free tier with massive context window (up to 1M tokens) and zero cost.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Prompt or large document analysis task' },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_omniroute_council',
    description: 'Query any of the 1,000+ models or smart auto-fallbacks (auto/best-coding, auto/best-reasoning, auto/fast, auto/best-free) via AetherBridge OmniRoute.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Prompt to send' },
        model: { 
          type: 'string', 
          description: 'Model identifier or combo (e.g. "auto/best-coding", "auto/best-reasoning", "auto/fast", "auto/best-free", "claude-3-7-sonnet", "deepseek-r1")' 
        },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_ollama_local',
    description: 'Execute prompt completely offline using local models in Ollama on Apple Silicon M2: "qwen2.5-coder:3b" (coding at 42 tok/s), "deepseek-r1:1.5b" (reasoning at 75 tok/s), or "llama3.2:latest" (general).',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'The prompt to process offline' },
        model: { type: 'string', description: 'Local model name: "qwen2.5-coder:3b", "deepseek-r1:1.5b", or "llama3.2:latest" (default: "qwen2.5-coder:3b")' }
      }
    }
  },
  {
    name: 'list_ecosystem_models',
    description: 'List available models and smart combos from AetherBridge OmniRoute (1,000+ providers) and local Ollama.',
    inputSchema: {
      type: 'object',
      properties: {
        filter: { type: 'string', description: 'Optional keyword to filter models (e.g. "claude", "coding", "llama")' }
      }
    }
  },
  {
    name: 'sandwich_orchestration',
    description: 'Sandwich Architecture: Gemini acts as the bread (evaluates latency vs quality) and dynamically delegates to the optimal ingredient (Claude Sonnet or Qwen Coder for code, DeepSeek R1 for reasoning, Groq LPU for sub-250ms speed, Claude Opus for architecture).',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'The task or question to process' },
        mode: { 
          type: 'string', 
          description: 'Optional execution mode: "auto" (default), "speed" (hyper-fast LPUs), "coding" (Claude Sonnet), "reasoning" (DeepSeek R1), "architecture" (Claude Opus), "offline" (Ollama)' 
        },
        system: { type: 'string', description: 'Optional system context' }
      }
    }
  }
];

async function callOmniRouteChat(model, prompt, system) {
  const messages = [];
  if (system) messages.push({ role: 'system', content: system });
  messages.push({ role: 'user', content: prompt });

  const res = await httpRequest(`${OMNIROUTE_URL}/v1/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${OMNIROUTE_TOKEN}`
    }
  }, { model, messages });

  if (res.data && res.data.choices && res.data.choices[0]) {
    return res.data.choices[0].message.content;
  }
  if (res.data && res.data.error) {
    throw new Error(res.data.error.message || JSON.stringify(res.data.error));
  }
  return JSON.stringify(res.data);
}

async function handleToolCall(name, args) {
  try {
    if (name === 'ask_claude_opus') {
      const output = await callOmniRouteChat('auto/claude-opus', args.prompt, args.system);
      return { content: [{ type: 'text', text: `[Claude Opus Response via OmniRoute]:\n\n${output}` }] };
    }

    if (name === 'ask_claude_sonnet') {
      const output = await callOmniRouteChat('claude-3-5-sonnet-latest', args.prompt, args.system);
      return { content: [{ type: 'text', text: `[Claude Sonnet Response via OmniRoute]:\n\n${output}` }] };
    }

    if (name === 'ask_deepseek_r1_reasoning') {
      const output = await callOmniRouteChat('deepseek-r1', args.prompt, args.system);
      return { content: [{ type: 'text', text: `[DeepSeek R1 Reasoning via OmniRoute]:\n\n${output}` }] };
    }

    if (name === 'ask_gemini_frontier') {
      const output = await callOmniRouteChat('gemini/gemini-3.1-flash-lite', args.prompt, args.system);
      return { content: [{ type: 'text', text: `[Gemini 3.1 Flash Lite via OmniRoute]:\n\n${output}` }] };
    }

    if (name === 'ask_omniroute_council') {
      const model = args.model || 'auto/best-coding';
      const output = await callOmniRouteChat(model, args.prompt, args.system);
      return { content: [{ type: 'text', text: `[OmniRoute (${model}) Response]:\n\n${output}` }] };
    }

    if (name === 'ask_ollama_local') {
      let model = args.model || 'qwen2.5-coder:3b';
      if (model === 'qwen' || model === 'coder') model = 'qwen2.5-coder:3b';
      if (model === 'r1' || model === 'deepseek') model = 'deepseek-r1:1.5b';
      if (model === 'llama') model = 'llama3.2:latest';

      const res = await httpRequest(`${OLLAMA_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }, { model, prompt: args.prompt, stream: false });

      if (res.data && res.data.response) {
        return { content: [{ type: 'text', text: `[Ollama Local (${model}) Offline Response]:\n\n${res.data.response}` }] };
      }
      return { content: [{ type: 'text', text: JSON.stringify(res.data) }] };
    }

    if (name === 'list_ecosystem_models') {
      const res = await httpRequest(`${OMNIROUTE_URL}/v1/models`, {
        headers: { 'Authorization': `Bearer ${OMNIROUTE_TOKEN}` }
      });
      let models = (res.data && res.data.data) ? res.data.data.map(m => m.id) : [];
      if (args && args.filter) {
        const f = args.filter.toLowerCase();
        models = models.filter(m => m.toLowerCase().includes(f));
      }
      const topCombos = [
        'auto/claude-opus', 'auto/claude-sonnet', 'auto/claude-haiku',
        'auto/best-coding', 'auto/best-reasoning', 'auto/best-fast',
        'auto/best-free', 'qwen2.5-coder:3b (Ollama Local)', 'deepseek-r1:1.5b (Ollama Local)', 'llama3.2:latest (Ollama Local)'
      ];
      return {
        content: [{
          type: 'text',
          text: `Total models in OmniRoute catalog: ${models.length}\n\nTop Recommended Routing Targets:\n- ${topCombos.join('\n- ')}\n\nMatched Models:\n${models.slice(0, 30).join('\n')}`
        }]
      };
    }

    if (name === 'sandwich_orchestration') {
      const mode = args.mode || 'auto';
      const prompt = args.prompt || '';
      const { execFileSync } = require('child_process');
      const scriptPath = require('path').join(__dirname, 'gemini_sandwich.py');
      const pyArgs = ['--mode', mode, prompt];
      try {
        const out = execFileSync('python3', [scriptPath, ...pyArgs], { encoding: 'utf-8', timeout: 90000 });
        const parsed = JSON.parse(out);
        const header = `[🥪 Gemini Sandwich Pipeline — Ingrediente: ${parsed.target_model} (${parsed.elapsed_sec}s)]:`;
        return {
          content: [{
            type: 'text',
            text: `${header}\n\n${parsed.content || parsed.error || JSON.stringify(parsed)}`
          }]
        };
      } catch (e) {
        return {
          isError: true,
          content: [{ type: 'text', text: `Sandwich execution error: ${e.message}` }]
        };
      }
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (err) {
    return {
      isError: true,
      content: [{ type: 'text', text: `Tool error (${name}): ${err.message}` }]
    };
  }
}

const rl = readline.createInterface({ input: process.stdin, output: process.stdout, terminal: false });

rl.on('line', async (line) => {
  if (!line.trim()) return;
  try {
    const req = JSON.parse(line);
    const { id, method, params } = req;

    if (method === 'initialize') {
      const resp = {
        jsonrpc: '2.0',
        id,
        result: {
          protocolVersion: '2024-11-05',
          capabilities: { tools: {} },
          serverInfo: { name: 'omniroute-mcp-bridge', version: '2.0.0' }
        }
      };
      process.stdout.write(JSON.stringify(resp) + '\n');
      return;
    }

    if (method === 'notifications/initialized') {
      return;
    }

    if (method === 'tools/list') {
      const resp = {
        jsonrpc: '2.0',
        id,
        result: { tools: TOOLS }
      };
      process.stdout.write(JSON.stringify(resp) + '\n');
      return;
    }

    if (method === 'tools/call') {
      const result = await handleToolCall(params.name, params.arguments || {});
      const resp = {
        jsonrpc: '2.0',
        id,
        result
      };
      process.stdout.write(JSON.stringify(resp) + '\n');
      return;
    }

    process.stdout.write(JSON.stringify({
      jsonrpc: '2.0',
      id,
      error: { code: -32601, message: `Method not found: ${method}` }
    }) + '\n');
  } catch (err) {
    process.stderr.write(`Bridge error: ${err.message}\n`);
  }
});
