# Soup (MakazhanAlpamys/Soup) - research for row 61

Read at commit bd963eaf (cloned 2026-10-15, read only, nothing run). Sources: README.md, docs/serving-and-export.md, docs/data.md, pyproject.toml, src/soup_cli/utils/gpu.py.

## What it is
README: "Fine-tune and post-train LLMs in one command. No SSH, no config hell." It is a Python CLI (soup-cli on PyPI) that wraps torch, transformers, peft, trl. Primary job: fine tuning (LoRA/QLoRA, SFT, DPO, GRPO, ...). It also has `soup serve` (OpenAI-compatible server, plus a `POST /v1/messages` Anthropic-shaped endpoint), `soup export --format gguf` "for Ollama / llama.cpp", `soup ingest` (turns Langfuse/LangSmith/Helicone trace exports into training data), and a huge extra surface (compliance, eval, adapters, "data flywheel").
It is NOT a model catalog, NOT a hosted provider, NOT a router. It provides no open models by itself; you bring a base model from HuggingFace and train it.

## Hardware vs the Vivobook (AMD, no NVIDIA)
- README requirements: "GPU with CUDA (recommended), Apple Silicon (MPS), or CPU (experimental - very slow)".
- grep for rocm/amd/vulkan over README, docs/, gpu.py: zero hits. gpu.py detect_device only knows cuda, mps, mlx, cpu. (A ROCm build of torch answers torch.cuda.is_available(), so it might half work, but nothing documents or tests it, and ROCm on a laptop iGPU is unsupported by AMD in practice.)
- Headline claim is 8B on a 4 GB NVIDIA card (RTX 3050). Not applicable. Your path would be CPU, which README calls "very slow" and "for testing".
- Python 3.10-3.12 only (README); system Python on Arch is newer, so it needs pipx/uv with a pinned older Python.

## Could a model tuned on your sessions be a cheap worker?
In theory: ingest sessions -> SFT a small model (Qwen/Llama 1-8B) -> `soup export --format gguf` -> `ollama create` -> serve locally. In practice no:
- Training needs a GPU you lack; you would rent one (Colab T4 free tier, or paid cloud) - that is the only real cost, plus your time.
- Claude Code session logs are not a listed ingest source (Langfuse, LangSmith, Helicone, OpenPipe, OTLP). You would write a converter, and sessions hold client/work text (cheap-worker.md forbids sending that to free models; training on it is the same exposure).
- A 1-8B model tuned on your chats will not beat gpt-oss-120b (already your fb-ask model) for summarize/triage/extract. Fine tuning buys style/format, not capability.
- Running it locally on an AMD laptop with no usable GPU = CPU inference, slow.
- Plug-in point if you ever did: Ollama exposes OpenAI API -> LiteLLM `ollama/<name>` -> fb-ask. That part is easy and needs nothing from Soup.

## Cost, license, maintenance, install security
- License: Apache-2.0 (README badge and text "Soup is Apache-2.0 and free"). Free; donations asked.
- Maintenance: one maintainer ("built and maintained in the open on a single 4 GB laptop"), at v0.76, very fast churn, repeated "Breaking:" changes (configs that loaded can stop loading; unknown keys refused since v0.75). Expect upgrade pain.
- Install: `pip install soup-cli[train]` pulls torch, transformers, peft, trl, datasets (hundreds of MB to GBs, many transitive packages). Telemetry is opt-in (SOUP_TELEMETRY=1, default off) per README. The docs show real hardening effort (safetensors strict, env filtering for llama.cpp forwarding, signing), but it is a young single-author project with a very large surface; the supply-chain risk is the transitive ML stack plus fast release cadence. If ever tried: isolated pipx/uv env, pinned version, in a throwaway container.

## Verdict
Wrong tool for row 61. It trains models; it does not supply or route them, and it does not support your AMD laptop for training. Do not adopt.

## Alternatives (one line each)
1. Ollama Cloud free tier / claude-fb (what you have): zero setup, hosted open models; limits are the free quota. Keep.
2. LiteLLM routing (what fb-ask uses): one OpenAI-style call to many providers (Ollama, OpenRouter, Groq); add fallbacks/model lists in its config. Best fit to extend.
3. OpenRouter free models (`:free` suffix): many open models behind one key, via LiteLLM or direct; free tier has low daily request caps and variable uptime.
4. claude-code-router (musistudio): proxy that lets Claude Code itself send chosen request types (background, think, long context) to other providers; useful for routing Claude Code traffic, not for fb-ask text jobs.
5. Local Ollama on the laptop (CPU or Vulkan/ROCm if supported): private and offline, but small models and slow on this hardware; only worth it for tiny jobs (e.g. 1-3B for classify).
(Items 2-5 from general knowledge, not fetched in this run.)

## Best for row 61
Extend the existing LiteLLM setup behind fb-ask: add one or two more free routes (OpenRouter `:free` open models and/or another Ollama Cloud model) as fallbacks in the LiteLLM config, so exit code 3 (fall back) becomes rarer. No new tool, no GPU, no install.
