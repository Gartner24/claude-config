# Local coding model on the Vivobook S 14 (research 67, 2026-10-15)

Read-only. Nothing installed. Raw pages saved with curl in `.../scratchpad/research/raw/`.
Tags: [M] measured on this machine, [V] verified verbatim in a raw page fetched with curl, [S] seen only in a search excerpt (not re-fetched), [U] unverified (my knowledge or inference).

## 0. This machine [M]

- CPU: AMD Ryzen AI 9 365 w/ Radeon 880M (10 cores / 20 threads, AVX-512). Not an HX 370: the iGPU is the 880M (12 CU), the 890M has 16 CU. Every 890M number below is an UPPER bound for this laptop.
- GPU: Vulkan sees "AMD Radeon 880M Graphics (RADV STRIX1)", Mesa 26.2.3, Vulkan 1.4. /dev/kfd exists.
- NPU: PCI 64:00.1 "Neural Processing Unit", module `amdxdna` loaded, /dev/accel/accel0 exists. Kernel 7.2.7-arch1-1.
- RAM: 22 GB total, 10 used, 12 available, swap 7 GB with 6 GB already used (memory is already tight before any model loads). Memory pressure (PSI) is 0 right now.
- iGPU memory: VRAM carve-out 512 MB; GTT (the shared-RAM pool the GPU may use) = 12,125,253,632 bytes = about 11.3 GiB. So the GPU can hold about 11 GB of weights+KV unless the limit is raised.
- Installed: `ollama` 0.35.0 (Arch package `ollama` = CPU only; /usr/lib/ollama has only ggml-cpu libs, no vulkan/rocm), systemd service active, `ollama list` empty (so it only serves the cloud model for claude-fb). `opencode` v2.0.15 at ~/.opencode/bin. No ROCm packages, no `ollama-vulkan`.
- Not checked: battery (no BAT0 node), live temps.

## 1. Runtime for the iGPU

Ranking for this chip: llama.cpp Vulkan (RADV) ~= Ollama-vulkan (same ggml Vulkan code) > Ollama/llama.cpp ROCm (better prompt processing, worse generation) >> CPU. NPU is a different, small-model path.

- Ollama GPU support. [V] ollama docs/gpu.mdx lists, under Linux ROCm: "AMD Ryzen AI | `Ryzen AI Max+ 395` ... `Ryzen AI 9 HX 375` `Ryzen AI 9 HX 370` `Ryzen AI 9 365`" and in the LLVM table "gfx1150 | Ryzen AI 9 HX 375". It requires "AMD ROCm v7 driver on Linux". It also says "Vulkan is enabled by default when the backend is installed" and "OLLAMA_VULKAN=0 ... to disable".
- Arch packaging. [V] ArchWiki Ollama: "Install the ollama package, which provides a daemon, command line tool, and CPU inference. For GPU inference: Install ollama-vulkan ... ollama-rocm ..." and "On AMD GPUs from RDNA 3 onward, ollama-vulkan is usually faster and uses less power than ollama-rocm and avoids ROCm's unsupported-GPU issues". `pacman -Ss` [M] shows extra/ollama-vulkan 0.35.0-1 and extra/ollama-rocm 0.35.0-1 exist. Our current CPU-only install means any local model today runs on CPU.
- ROCm vs Vulkan on gfx1150, measured on a HX 370 (OneXPlayer, kernel 6.19, Mesa 25.3.6, llama.cpp b9282). [V] gfx1150-bench README: "Vulkan wins token generation in every cell ... ROCm wins prompt processing in every cell but one". Table (tg = tokens/s generated, pp = prompt tokens/s):
  - Qwen3-4B Q4_K_M: Vulkan tg 32.41, ROCm tg 21.86; pp 647 vs 671
  - Qwen3-4B Q8_0: tg 19.62 vs 14.87; pp 653 vs 765
  - Qwen2.5-Coder-14B Q4_0: tg 10.27 vs 8.28; pp 196 vs 269
  - Qwen2.5-Coder-14B Q4_K_M: tg 9.30 vs 7.42; pp 178 vs 212
  - Same README: "Token-generation ceiling = measured bandwidth (~96 GB/s) / weights read per token" and "Vulkan token generation sits at 82-91% of the memory-bandwidth wall". Generation speed is memory-bandwidth-bound, so tg ~= 96 GB/s / active-weight GB. This is the formula to predict any model.
  - Speculative decoding (1.5B draft for 14B): 9.54 -> 23.17 tg (2.43x) "ran at -c 1024 (GTT ceiling)". Only in llama.cpp (llama-server --model-draft), not in Ollama [U].
- 890M other numbers.
  - [V] llama.cpp PR 20334: Qwen3.5-4B Q4_K_M tg 21, pp-512 346; Qwen3.5-9B Q4_K_M tg 12, pp-512 249 (890M, Vulkan).
  - [V] llama.cpp issue 19976 comment: "TG Performance went up from 13 to 15 tg/s with ---n-cpu-moe 20 and gpt-oss:20B" (890M, with a PR build).
  - [V] Framework forum (HX 370, 96 GB RAM, 32 GB set to iGPU in BIOS, LM Studio Vulkan): "20-23 tok/sec ... using the openai/gpt-oss-20b model". That machine has far more GPU memory than ours.
  - [V] llama.cpp discussion 27051 (HX 370, Mesa 26.0.3, kernel 7.0): 12.43 GiB Q3 30B-class model, tg128 "3.21-3.32 tok/s" with default power policy, "7.01 +/- 0.02" with `echo high > /sys/class/drm/cardN/device/power_dpm_force_performance_level`. Cost on the same page: idle SoC 2.71 W (auto) vs 5.30 W (high); load ~33 W -> ~51 W, plateau 72 C for ten minutes; "`high` isn't persistent across reboot". Also in the thread: "Measured on Strix Point only".
  - Expect the 880M (12 CU vs 16 CU) at or below these. No 880M or Ryzen AI 9 365 specific figure was found. [U] Real figure only from our own test.
- Partial-offload path on 12 GB GTT. gpt-oss:20b is 14 GB [V ollama.com/library/gpt-oss: "gpt-oss:20b ... 14GB · 128K"]. It does not fit in 11.3 GiB GTT. Ollama splits layers between GPU and CPU automatically; llama.cpp has `--n-cpu-moe N` to keep the MoE expert tensors on CPU, which is the 13-15 tg/s case above. [U] raising GTT (`ttm.pages_limit` / `amdgpu.gttsize` kernel parameter) would help but eats the 22 GB shared with the desktop. Do not do it first.
- LM Studio. Works through Vulkan (Framework quote above). It is a closed-source GUI app, AppImage on Arch (AUR). Adds nothing over llama.cpp for headless use. Skip.
- Lemonade (AMD). [V] README: "Lemonade is the local AI server ... on your own NPU and GPU"; Arch badge "supported", `pacman -S lemonade-server` (docs/guide/install/arch.md, extra repo). Backend table: `llamacpp` with `vulkan` ("x86_64 CPU, AMD iGPU, AMD dGPU", Windows+Linux), `rocm` (Windows+Linux), `flm` on `npu` ("XDNA2 NPU", Windows, Linux), `ryzenai-llm` NPU Windows only, `vllm` and `ds4` Strix Halo only. It is an OpenAI-compatible server wrapping llama.cpp, so speed equals llama.cpp Vulkan. It is the only packaged route to the NPU on Linux. Worth trying only as a second step.
- NPU. [V] FastFlowLM README: "supports all Ryzen AI Series chips with XDNA2 NPUs (Strix, Strix Halo, Kraken, and Gorgon Point)", "Faster and over 10x more power-efficient", contexts "up to 256k". Our machine has the XDNA2 NPU and the `amdxdna` driver is already loaded [M]. I found no Linux tokens/s number for a 365-class NPU and no evidence the NPU models cover coding-agent-grade sizes; its models are small (single digit B, plus some MoE per its README). [U] Verdict: good for low-power small-model jobs (summaries), not a coding agent. Needs `xrt` and the FLM build from AUR (not installed).

## 2. Models for ~11 GiB GPU pool / 12 GB free RAM

Speed rule: tg ~= 0.85 x 96 GB/s / (bytes read per token). Dense models read all weights; MoE read only the active experts. Sizes are Ollama library tags [V].

| Model | Disk size [V] | Active | Predicted tg here | Fit |
|---|---|---|---|---|
| qwen3:4b / qwen3.5-4B Q4 | ~2.5 GB | 4B | 20-30 [V: 21-32 on 890M] | easy, weak at agentic work |
| qwen2.5-coder 14B Q4_K_M | ~9 GB | 14B | ~7-9 [V: 9.3 on 890M] | fits GTT, tight with a long context |
| gpt-oss:20b (MXFP4) | 14 GB | 3.6B active [U] | 13-15 with `--n-cpu-moe` [V on 890M]; 20-23 only with 32 GB iGPU memory | does NOT fit GPU pool, spills to CPU, needs ~14 GB RAM for weights, we have 12 GB available (swap already used) |
| qwen3-coder:30b (A3B) | 19 GB [V] | 3.3B [V] | maybe 8-15 [U] | does not fit RAM headroom; Q3 variants (~12-13 GiB) ran 7 tok/s on 890M [V disc 27051] |
| devstral:24b | 14 GB [V] | 24B dense | ~5-6 [U, 96/14*0.85=5.8] | fits barely, too slow for agent loops |
| gemma-class 4B-12B | 3-8 GB | dense | like the dense rows | not tool-calling strong [U] |

- Quantization: Q4_K_M is the default sweet spot. [V] bench: Q4_0 is faster than Q4_K_M by ~10% on generation (10.27 vs 9.30 for 14B); Q8 costs 2x bandwidth.
- Context: [V] Ollama docs "Ollama defaults to ... < 24 GiB VRAM: 4k context ... Tasks which require large context like web search, agents, and coding tools should be set to at least 64000 tokens." Claude Code integration page [V]: "Choose a model and set a 64k+ context window." KV cache at 64k on top of 9-14 GB weights will not fit in 12 GB free RAM next to a desktop. Realistic here: 16k-32k context. The spec-decode run above used `-c 1024` because of the GTT ceiling.
- Tool calling quality [U unless noted]: Ollama tags `tools` exist for gpt-oss, qwen3-coder, devstral [V: "tools" label on library pages]. gpt-oss:20b has the best tool-call reliability of what fits; qwen3-coder has had XML tool-format bugs in some servers; small dense 4B models loop or drop arguments. [V] opencode docs: "If tool calls aren't working, try increasing `num_ctx` in Ollama. Start around 16k - 32k."
- SWE-bench Verified, only what I verified: [V] Devstral Small (24B, May 2025 version on Ollama) 46.8% in the OpenHands scaffold, versus "Claude 3.5 Haiku Anthropic Scaffold 40.6" on the same page. gpt-oss-20b ~60% and Qwen3-Coder-30B-A3B ~50% are [U]; I did not fetch them. Anything in the 4B-14B range scores far below current Claude models; the gap to Claude Sonnet/Opus 4.x class (70%+ [U]) is large.

## 3. Agent front end

Anthropic status [user-supplied, not re-checked on the page]: routing Claude Code to non-Claude models through a gateway is unsupported. My grep of code.claude.com/docs/en/llm-gateway and model-config for "unsupported/not supported" found nothing, so I cannot quote it either way. Counter-evidence [V]: docs.ollama.com/integrations/claude-code says "Ollama connects Claude Code to local and cloud models through its Anthropic-compatible API ... `ollama launch claude`" and "Choose a model and set a 64k+ context window". So it works technically; the support position stays "not supported by Anthropic".

Options:
1. opencode (already installed, v2.0.15). Native local support. [V] opencode providers doc:
```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": { "ollama": {
    "npm": "@ai-sdk/openai-compatible",
    "name": "Ollama (local)",
    "options": { "baseURL": "http://localhost:11434/v1" },
    "models": { "llama2": { "name": "Llama 2" } } } }
}
```
   "Ollama can automatically configure itself for OpenCode" (`ollama launch opencode --model qwen3-coder` appears on the library pages [V]). Set the model entry to `gpt-oss:20b`. No Claude Code involvement, no gateway question. Best fit for "agent over a local model".
2. Claude Code via claude-fb with a new LiteLLM entry. Works mechanically (LiteLLM already speaks to http://localhost:11434 for the cloud model). Pitfalls: Claude Code sends a ~15-20k token system prompt + tool schemas [U], which on this iGPU is minutes of prefill (pp ~100-250 tok/s) before the first token, and needs 64k context [V Ollama doc] that does not fit. Not recommended as the agent.
3. aider: works with `ollama_chat/<model>`, repo-map + diff edits are friendlier to weak models and need no tool calling [U]. `OLLAMA_API_BASE=http://127.0.0.1:11434`, `aider --model ollama_chat/qwen2.5-coder:14b`. Good second choice for small-model edits.
4. Others (Continue, Cline, Goose): not evaluated.

Pitfalls to expect [mix]: Ollama default context 4k [V] silently truncates the agent prompt (the usual cause of "tool calls not working"); set `OLLAMA_CONTEXT_LENGTH=16384` or per-model `num_ctx` [U for the env var name, matches the ctx doc topic]; keep `OLLAMA_KEEP_ALIVE` short so the model unloads and returns RAM; `OLLAMA_NUM_PARALLEL=1`.

## 4. Good for / bad at

Good:
- Offline fallback when the network or the cloud quota is gone (claude-fb already covers quota; local covers offline).
- fb-ask jobs at zero marginal cost: summarize/triage/extract/classify/commit-msg. Short inputs (under ~4k tokens) work on a 4B-14B model. fb-ask is already for inputs over ~20,000 characters (~5k tokens), which at 100-250 tok/s prefill is 20-50 s per job: usable for batch.
- Privacy: nothing leaves the machine. The cheap-worker rule currently refuses client/work repos; a local tier could lift that for those repos, since the reason for the refusal (text going to a third party) is gone. That is a policy change, ask before doing it.

Bad:
- Speed: 7-15 tok/s generation, prompt processing 100-250 tok/s on 14B-class; an agent loop with 30k-token context re-reads costs minutes per step. The current cloud setup runs gpt-oss:120b at provider speed.
- Quality: current fb path is a 120B model; local fits ~20B at best (and gpt-oss:20b barely fits). Expect the gap seen between gpt-oss-120b and 20b, plus another to Claude.
- Memory: only 12 GB of 22 GB free at this moment with swap in use.

## 5. Battery / heat / RAM [mostly U; one V source]

- [V] Measured on HX 370: load ~33-54 W SoC and ~72 C plateau in a 10-minute soak at 7 tok/s on a 12 GB model; `high` DPM adds ~2.6 W idle. The 880M in a thin ASUS chassis will draw somewhat less and clock lower [U]. On battery expect ~1 h of continuous generation [U inference], plus fans.
- Memory: GPU weights live in GTT (system RAM). A 14 GB gpt-oss:20b resident takes ~14 of 22 GB; with Claude Code sessions, wf runner worktrees/test runs and the KDE desktop already using 10 GB, that pushes swap hard (swap already 6 of 7 GB used [M]). 9 GB (14B Q4) or 2.5 GB (4B) are the sizes that coexist with sessions.
- Concurrency: the wf runner and a local model contend for the same memory bandwidth and thermals; generation slows for both. Do not run a local agent during `wf run`. Use `OLLAMA_KEEP_ALIVE=2m` so idle sessions free the RAM.
- Ollama must keep serving the cloud model for claude-fb on port 11434; adding a local tag to the same daemon does not change that, but a local model load takes the memory.

## 6. Recommendation

Verdict: worth a 30-minute trial as an OFFLINE / PRIVATE tier, not as a replacement. Do not wire it as claude-fb order 1 or as the Claude Code backend.

Install (needs the user's sudo, none done):
1. `sudo pacman -S ollama-vulkan` (adds the Vulkan backend to the existing daemon, keeps the cloud route; ArchWiki says it is usually faster than ollama-rocm on RDNA3+). Add the `ollama` user to `render` and `video` groups (Ollama gpu doc: "you may need to add the `ollama` user to the `render` group"). `sudo systemctl restart ollama`. Check `journalctl -u ollama -n 50` shows "Vulkan" and the 880M.
2. Raise GPU clocks for the test only: `echo high | sudo tee /sys/class/drm/card1/device/power_dpm_force_performance_level` (card index: card1 here [M]; reverts at reboot [V]). Plug in AC.
3. Models: `ollama pull qwen2.5-coder:14b` (~9 GB) and `ollama pull gpt-oss:20b` (14 GB). Start with the 14B.
4. For the test only set context: a Modelfile `PARAMETER num_ctx 16384` or `OLLAMA_CONTEXT_LENGTH=16384` on the service.

Fixed test (same every time, so numbers compare):
- Speed: `ollama run qwen2.5-coder:14b --verbose "..."` with a fixed 400-word prompt; record "prompt eval rate" and "eval rate" (tok/s). Repeat for gpt-oss:20b. Record `free -g`, `sensors`, and whether `ollama ps` says 100% GPU or a CPU/GPU split.
- Quality: one fixed task from our own work: "In repo X, add a unit test for function Y (point to a real small function) and make it pass", run in opencode with the config above, once with each model, plus the same task through the existing claude-fb gpt-oss:120b. Score: test passes (yes/no), number of tool-call errors, wall clock, number of retries by hand. Do the mutation check from lessons.md on the produced test.
- Decision rule: adopt local for fb-ask only if the 14B passes a 10-item classify/extract sample with at most 1 miss versus the cloud answer, and median job time is under ~30 s. Adopt for agent work only if the fixed task passes in under 15 minutes without hand fixes; I expect it will not [U].

Plugging into the existing setup (after the test passes):
- litellm.yaml: add a model group, not an extra order in fb-safe, so an offline machine does not silently fall to a slow model for every call:
```yaml
  - model_name: fb-local
    litellm_params: {model: ollama_chat/qwen2.5-coder:14b, api_base: "http://localhost:11434"}
```
  Then `fb-ask --model fb-local` (or its equivalent flag; I did not read the fb-ask source, name unverified) for private text and for offline use; claude-fb stays on fb-safe. For true offline failover, append `fb-local` as order 3 of fb-safe only if you accept slow, lower-quality answers on failure. This is your decision; the order list in the yaml is a policy choice, not mine.
- Agent work: use opencode with the provider block above (a separate window), not Claude Code.
- If the 14B is too slow: drop to qwen3 4B (about 3x faster) for fb-ask-style jobs only.
- Revisit later: Lemonade (`pacman -S lemonade-server`) for the NPU backend, once someone reports Linux NPU tokens/s on a Ryzen AI 9 365; and a kernel GTT bump if you decide to dedicate more RAM.

## Gaps and caveats
- No Radeon 880M / Ryzen AI 9 365 specific benchmark found; all measurements are 890M (HX 370), 33% more compute units. Memory bandwidth is the limit for generation, so 880M tg should be close for decode and lower for prompt processing.
- gpt-oss-20b SWE-bench and Qwen3-Coder-30B SWE-bench scores not verified; only Devstral's 46.8% was.
- Anthropic "unsupported gateway" claim not located in the raw docs I grepped; taken from your message.
- Firecrawl hit its free rate limit and searxng engines failed; sources came from Exa search excerpts (tagged [S] where not re-fetched) and curl of raw pages.
- Battery, temperature and exact token rates on this laptop: not measured, no software installed.
