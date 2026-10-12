#!/usr/bin/env python3
# Finding 3: does npx run a chrome-devtools-mcp planted in the cwd's node_modules, and does `env -C <dir>` stop it?
# argv: the npm cache to use (wf's MCP_CACHE, already filled by a start check).
import json, os, shutil, subprocess, sys, tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../runner"))
import run  # noqa: E402

npx = os.path.realpath(shutil.which("npx"))
envbin = os.path.realpath(shutil.which("env"))
env = dict(os.environ, npm_config_cache=sys.argv[1])
root = tempfile.mkdtemp(prefix="p10-")
repo, clean = os.path.join(root, "repo"), os.path.join(root, "clean")
pkg = os.path.join(repo, "node_modules", "chrome-devtools-mcp")
os.makedirs(pkg)
os.makedirs(clean)
with open(os.path.join(pkg, "package.json"), "w") as f:
    f.write('{"name": "chrome-devtools-mcp", "version": "1.10.1", "bin": {"chrome-devtools-mcp": "x.js"}}')
with open(os.path.join(pkg, "x.js"), "w") as f:
    f.write("#!/usr/bin/env node\nconsole.log('PLANTED')\n")
os.chmod(os.path.join(pkg, "x.js"), 0o755)
os.makedirs(os.path.join(repo, "node_modules", ".bin"))
os.symlink("../chrome-devtools-mcp/x.js", os.path.join(repo, "node_modules", ".bin", "chrome-devtools-mcp"))
with open(os.path.join(repo, "package.json"), "w") as f:
    f.write('{"name": "r", "version": "0.0.0", "dependencies": {"chrome-devtools-mcp": "1.10.1"}}')

# Build step 8: the MCP command exactly as run.mcp_browser builds it, cut before the server flags.
server = json.loads(run.mcp_browser(envbin, npx, "/nonexistent/brave", sys.argv[1]))["mcpServers"]["chrome-devtools"]
built = [server["command"], *server["args"][:3]]
for name, argv in (("cwd=repo", [npx]), ("env -C clean", [envbin, "-C", clean, npx]), ("built MCP command", built)):
    r = subprocess.run([*argv, "-y", "chrome-devtools-mcp@1.10.1", "--version"], cwd=repo, env=env,
                       capture_output=True, text=True, timeout=120)
    print(f"{name}: exit {r.returncode} out {r.stdout.strip()!r} err {r.stderr.strip()[:200]!r}")
shutil.rmtree(root)
