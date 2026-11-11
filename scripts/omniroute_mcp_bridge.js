#!/usr/bin/env node
/**
 * OmniRoute Unified Model Context Protocol (MCP) Bridge for Antigravity & Claude Desktop
 * Routes directly through OmniRoute - AetherBridge ($0 free cloud tiers + smart combos).
 * Local Ollama is strictly optional and only invoked if active at OLLAMA_URL.
 */

const fs = require('fs');
const http = require('http');
const os = require('os');
const readline = require('readline');
const path = require('path');
const { execFileSync } = require('child_process');

function readEnvToken(filePath, keys) {
  try {
    if (!fs.existsSync(filePath)) return '';
    const lines = fs.readFileSync(filePath, 'utf-8').split(/\r?\n/);
    for (const raw of lines) {
      const line = raw.trim();
      if (!line || line.startsWith('#') || !line.includes('=')) continue;
      const idx = line.indexOf('=');
      const k = line.slice(0, idx).trim();
      if (keys.includes(k)) {
        const val = line.slice(idx + 1).trim().replace(/^["']|["']$/g, '');
        if (val) return val;
      }
    }
  } catch (_) {}
  return '';
}

function resolveOmniRouteToken() {
  const fromEnv =
    process.env.OMNIROUTE_API_KEY ||
    process.env.OMNIROUTE_TOKEN ||
    process.env.OMNIROUTE_LOCAL_TOKEN;
  if (fromEnv) return fromEnv;

  const repoRoot = path.resolve(__dirname, '..');
  return (
    readEnvToken(path.join(os.homedir(), '.omniroute', '.env'), ['OMNIROUTE_API_KEY', 'OMNIROUTE_LOCAL_TOKEN']) ||
    readEnvToken(path.join(repoRoot, 'api_keys.env'), ['OMNIROUTE_API_KEY', 'OMNIROUTE_LOCAL_TOKEN']) ||
    'omniroute-secret-key-local'
  );
}

const OMNIROUTE_URL = process.env.OMNIROUTE_URL || 'http://127.0.0.1:20128';
const OMNIROUTE_TOKEN = resolveOmniRouteToken();
const OLLAMA_URL = process.env.OLLAMA_URL || 'http://127.0.0.1:11434';

function httpRequest(urlStr, options = {}, data = null, timeoutMs = 45000) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const reqOptions = {
      hostname: url.hostname,
      port: url.port,
      path: url.pathname + (url.search || ''),
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: timeoutMs
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

    req.on('timeout', () => {
      req.destroy(new Error(`Request timed out after ${timeoutMs}ms`));
    });
    req.on('error', reject);
    if (data) {
      req.write(typeof data === 'string' ? data : JSON.stringify(data));
    }
    req.end();
  });
}

async function isOllamaAlive() {
  try {
    const res = await httpRequest(`${OLLAMA_URL}/api/tags`, {}, null, 600);
    return res.status === 200;
  } catch (_) {
    return false;
  }
}

const TOOLS = [
  {
    name: 'ask_deepseek_v4_r2',
    description: 'Dispatch cutting-edge mathematical reasoning, complex logic, or elite coding via OmniRoute direct cloud cascade.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Mathematical proof, algorithmic problem, or coding task' },
        variant: {
          type: 'string',
          description: 'Model variant: "deepseek-v4-pro", "deepseek-v4-flash", or "deepseek-r2"'
        },
        system: { type: 'string', description: 'Optional system context' }
      }
    }
  },
  {
    name: 'ask_glm_family',
    description: 'Dispatch macro-architecture, systems design, and synthesis via OmniRoute cloud gateway.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Complex architecture design, system evaluation, or agent task' },
        variant: {
          type: 'string',
          description: 'Variant: "glm-5.3-flash" (default), "glm-5.2", or "glm-5.1"'
        },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_kimi_moonshot',
    description: 'Dispatch long-context repository comprehension and document analysis via OmniRoute.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Task requiring long context or deep reading' },
        variant: { type: 'string', description: 'Variant: "kimi-k3" (default) or "kimi-k2.6"' },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_qwen_3_coder',
    description: 'Dispatch multi-file code generation, refactoring, and debugging via OmniRoute coding cascade.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Code implementation, debugging, or repository refactoring' },
        variant: { type: 'string', description: 'Variant: "qwen-3.6-coder" (default) or "qwen-3-235b"' },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_gemini_2_5',
    description: 'Query Google Gemini directly through OmniRoute for 1M+ context and rapid multimodal reasoning.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Prompt or large document analysis task' },
        variant: { type: 'string', description: 'Variant: "gemini-2.5-pro" or "gemini-2.5-flash"' },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_nemotron_ultra',
    description: 'Query NVIDIA Nemotron 3 Ultra 550B via OmniRoute (NVIDIA NIM & OpenRouter free tier).',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Engineering or reasoning prompt' },
        variant: { type: 'string', description: 'Variant: "nemotron-3-ultra" (default) or "gpt-oss-120b"' },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_claude_opus',
    description: 'Dispatch an architectural or deep reasoning task to OmniRoute Opus combo (claude-opus-5-5).',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'The complex problem or architectural design prompt' },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_claude_sonnet',
    description: 'Dispatch coding, debugging, or engineering tasks to OmniRoute Sonnet combo (claude-sonnet-5-5).',
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
    description: 'Execute deep mathematical and logical reasoning via OmniRoute reasoning cascade.',
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
    description: 'Query Google Gemini 3.5 Flash / 3.1 Flash Lite via OmniRoute with 1M context window and zero cost.',
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
    description: 'Query any of the 1,000+ models or smart combos (claude-sonnet-5-5, claude-opus-5-5, claude-haiku-5-5, auto/best-coding, auto/best-reasoning, auto/best-fast) via OmniRoute.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'Prompt to send' },
        model: {
          type: 'string',
          description: 'Model identifier or combo (e.g. "claude-sonnet-5-5", "claude-opus-5-5", "auto/best-coding", "nvidia/nvidia/nemotron-3-ultra-550b-a55b", "gemini/gemini-3.5-flash")'
        },
        system: { type: 'string', description: 'Optional system prompt' }
      }
    }
  },
  {
    name: 'ask_ollama_local',
    description: 'Optional: Execute prompt locally via Ollama ONLY if Ollama is installed and running on localhost:11434.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'The prompt to process offline' },
        model: { type: 'string', description: 'Local model name (default: "llama3.2:latest")' }
      }
    }
  },
  {
    name: 'list_ecosystem_models',
    description: 'List live models and smart combos from AetherBridge OmniRoute gateway.',
    inputSchema: {
      type: 'object',
      properties: {
        filter: { type: 'string', description: 'Optional keyword to filter models (e.g. "gemini", "nemotron", "claude", "free")' }
      }
    }
  },
  {
    name: 'sandwich_orchestration',
    description: 'Sandwich Architecture: Gemini evaluates latency vs quality and delegates to the optimal direct OmniRoute cloud specialist.',
    inputSchema: {
      type: 'object',
      required: ['prompt'],
      properties: {
        prompt: { type: 'string', description: 'The task or question to process' },
        mode: {
          type: 'string',
          description: 'Execution mode or target: "auto" (default), "opus", "sonnet", "haiku", "nemotron", "gemini25", "speed", "coding", "reasoning", "architecture"'
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
  throw new Error(`Unexpected gateway response: ${JSON.stringify(res.data)}`);
}

async function callOmniRouteWithFallback(candidates, prompt, system) {
  let lastErr = null;
  for (const model of candidates) {
    try {
      const output = await callOmniRouteChat(model, prompt, system);
      return { model, output };
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr || new Error('All OmniRoute candidates failed');
}

async function handleToolCall(name, args) {
  try {
    if (name === 'ask_deepseek_v4_r2') {
      const variant = args.variant || 'deepseek-v4-pro';
      const cands = variant.includes('flash')
        ? ['oc/deepseek-v4-flash-free', 'cfp/deepseek-ai/deepseek-v4-flash-0731', 'claude-sonnet-5-5', 'gemini/gemini-3.5-flash']
        : ['cfp/deepseek-ai/deepseek-v4-pro-0813', 'claude-opus-5-5', 'nvidia/nvidia/nemotron-3-ultra-550b-a55b', 'auto/best-reasoning'];
      const { model, output } = await callOmniRouteWithFallback(cands, args.prompt, args.system);
      return { content: [{ type: 'text', text: `[OmniRoute (${model}) Response]:\n\n${output}` }] };
    }

    if (name === 'ask_glm_family') {
      const cands = ['nvidia/z-ai/glm-5.3-flash', 'claude-opus-5-5', 'nvidia/nvidia/nemotron-3-ultra-550b-a55b', 'gemini/gemini-3.5-flash'];
      const { model, output } = await callOmniRouteWithFallback(cands, args.prompt, args.system);
      return { content: [{ type: 'text', text: `[OmniRoute (${model}) Response]:\n\n${output}` }] };
    }

    if (name === 'ask_kimi_moonshot') {
      const cands = ['claude-sonnet-5-5', 'gemini/gemini-3.5-flash', 'gemini/gemini-3.1-flash-lite'];
      const { model, output } = await callOmniRouteWithFallback(cands, args.prompt, args.system);
      return { content: [{ type: 'text', text: `[OmniRoute (${model}) Response]:\n\n${output}` }] };
    }

    if (name === 'ask_qwen_3_coder') {
      const cands = ['auto/best-coding', 'claude-sonnet-5-5', 'nvidia/google/gemma-4-31b-it', 'openrouter/cohere/north-mini-code:free'];
      const { model, output } = await callOmniRouteWithFallback(cands, args.prompt, args.system);
      return { content: [{ type: 'text', text: `[OmniRoute (${model}) Response]:\n\n${output}` }] };
    }

    if (name === 'ask_gemini_2_5') {
      const variant = args.variant || 'gemini-2.5-pro';
      const cands = variant.includes('flash')
        ? ['gemini/gemini-3.1-flash-lite', 'gemini/gemini-3.5-flash', 'claude-haiku-5-5']
        : ['gemini/gemini-3.5-flash', 'gemini/gemini-3.1-flash-lite', 'claude-sonnet-5-5'];
      const { model, output } = await callOmniRouteWithFallback(cands, args.prompt, args.system);
      return { content: [{ type: 'text', text: `[Gemini via OmniRoute (${model})]:\n\n${output}` }] };
    }

    if (name === 'ask_nemotron_ultra') {
      const cands = [
        'nvidia/nvidia/nemotron-3-ultra-550b-a55b',
        'openrouter/nvidia/nemotron-3-ultra-550b-a55b:free',
        'claude-opus-5-5'
      ];
      const { model, output } = await callOmniRouteWithFallback(cands, args.prompt, args.system);
      return { content: [{ type: 'text', text: `[Nemotron (${model}) Response]:\n\n${output}` }] };
    }

    if (name === 'ask_claude_opus') {
      const { model, output } = await callOmniRouteWithFallback(['claude-opus-5-5', 'auto/claude-opus', 'nvidia/nvidia/nemotron-3-ultra-550b-a55b'], args.prompt, args.system);
      return { content: [{ type: 'text', text: `[OmniRoute Opus (${model})]:\n\n${output}` }] };
    }

    if (name === 'ask_claude_sonnet') {
      const { model, output } = await callOmniRouteWithFallback(['claude-sonnet-5-5', 'auto/best-coding', 'gemini/gemini-3.5-flash'], args.prompt, args.system);
      return { content: [{ type: 'text', text: `[OmniRoute Sonnet (${model})]:\n\n${output}` }] };
    }

    if (name === 'ask_deepseek_r1_reasoning') {
      const { model, output } = await callOmniRouteWithFallback(['auto/best-reasoning', 'claude-opus-5-5', 'nvidia/nvidia/nemotron-3-ultra-550b-a55b'], args.prompt, args.system);
      return { content: [{ type: 'text', text: `[OmniRoute Reasoning (${model})]:\n\n${output}` }] };
    }

    if (name === 'ask_gemini_frontier') {
      const { model, output } = await callOmniRouteWithFallback(['gemini/gemini-3.5-flash', 'gemini/gemini-3.1-flash-lite'], args.prompt, args.system);
      return { content: [{ type: 'text', text: `[OmniRoute Gemini (${model})]:\n\n${output}` }] };
    }

    if (name === 'ask_omniroute_council') {
      const requested = args.model || 'claude-sonnet-5-5';
      const { model, output } = await callOmniRouteWithFallback([requested, 'claude-sonnet-5-5', 'openrouter/auto'], args.prompt, args.system);
      return { content: [{ type: 'text', text: `[OmniRoute (${model}) Response]:\n\n${output}` }] };
    }

    if (name === 'ask_ollama_local') {
      const alive = await isOllamaAlive();
      if (!alive) {
        return {
          content: [{
            type: 'text',
            text: '[AetherBridge Notice]: Ollama no está instalado ni activo en este equipo. Usa ask_omniroute_council o sandwich_orchestration para consultar directamente los proveedores cloud en OmniRoute.'
          }]
        };
      }
      let model = args.model || 'llama3.2:latest';
      if (model === 'qwen' || model === 'coder') model = 'qwen2.5-coder:3b';
      if (model === 'r1' || model === 'deepseek') model = 'deepseek-r1:1.5b';
      if (model === 'llama') model = 'llama3.2:latest';

      const res = await httpRequest(`${OLLAMA_URL}/api/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }, { model, prompt: args.prompt, stream: false });

      if (res.data && res.data.response) {
        return { content: [{ type: 'text', text: `[Ollama Local (${model}) Response]:\n\n${res.data.response}` }] };
      }
      return { content: [{ type: 'text', text: JSON.stringify(res.data) }] };
    }

    if (name === 'list_ecosystem_models') {
      const topDirect = [
        'claude-sonnet-5-5 (Gemini 3.5 Flash -> Gemma 4 31B -> Nemotron 550B -> OpenRouter)',
        'claude-opus-5-5 (Nemotron 3 Ultra 550B -> Gemini 3.5 Flash -> OpenRouter)',
        'claude-haiku-5-5 (Gemini 3.1 Flash Lite -> Cohere North Mini -> Nemotron 3.5 Lightning)',
        'auto/best-coding / auto/best-reasoning / auto/best-fast',
        'nvidia/nvidia/nemotron-3-ultra-550b-a55b (NVIDIA NIM)',
        'nvidia/google/gemma-4-31b-it (NVIDIA NIM)',
        'gemini/gemini-3.5-flash / gemini/gemini-3.1-flash-lite (Google Gemini)',
        'openrouter/nvidia/nemotron-3-ultra-550b-a55b:free / openrouter/cohere/north-mini-code:free'
      ];
      const ollamaOnline = await isOllamaAlive();
      try {
        const res = await httpRequest(`${OMNIROUTE_URL}/v1/models`, {
          headers: { 'Authorization': `Bearer ${OMNIROUTE_TOKEN}` }
        });
        let models = (res.data && res.data.data) ? res.data.data.map(m => m.id) : [];
        if (args && args.filter) {
          const f = args.filter.toLowerCase();
          models = models.filter(m => m.toLowerCase().includes(f));
        }
        return {
          content: [{
            type: 'text',
            text: `OmniRoute - AetherBridge Direct Providers (Ollama local: ${ollamaOnline ? 'active' : 'not installed/disabled'}):\n- ${topDirect.join('\n- ')}\n\nLive Models in OmniRoute Gateway (${models.length} total):\n${models.slice(0, 35).join('\n')}`
          }]
        };
      } catch (e) {
        return {
          content: [{
            type: 'text',
            text: `OmniRoute - AetherBridge Direct Providers:\n- ${topDirect.join('\n- ')}\n\n(Gateway unreachable at ${OMNIROUTE_URL}: ${e.message})`
          }]
        };
      }
    }

    if (name === 'sandwich_orchestration') {
      const mode = args.mode || 'auto';
      const prompt = args.prompt || '';
      const scriptPath = path.join(__dirname, 'gemini_sandwich.py');
      const pyArgs = ['--mode', mode, prompt];
      try {
        const out = execFileSync('python3', [scriptPath, ...pyArgs], { encoding: 'utf-8', timeout: 90000 });
        const parsed = JSON.parse(out);
        const header = parsed.transparency_banner || `[🥪 Gemini Sandwich: ${parsed.target_model}]`;
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
      process.stdout.write(JSON.stringify({
        jsonrpc: '2.0',
        id,
        result: {
          protocolVersion: '2024-11-05',
          capabilities: { tools: {} },
          serverInfo: { name: 'omniroute-mcp-bridge', version: '2.6.0' }
        }
      }) + '\n');
      return;
    }

    if (method === 'notifications/initialized') return;

    if (method === 'tools/list') {
      process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id, result: { tools: TOOLS } }) + '\n');
      return;
    }

    if (method === 'tools/call') {
      const result = await handleToolCall(params.name, params.arguments || {});
      process.stdout.write(JSON.stringify({ jsonrpc: '2.0', id, result }) + '\n');
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
