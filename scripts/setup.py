#!/usr/bin/env python3
"""One-time setup: environment, vault + credential, agent.

Run this once. It writes ids.json with the resource IDs that launch_session.py
reuses on every run. Re-running with ids.json already present refuses to
proceed — update the agent in place instead (see bottom of this file).

Requires: pip install anthropic pyyaml
Requires ANTHROPIC_API_KEY set — either exported in your shell, or dropped
into .env in this project's root (edit that file directly in an editor; it's
gitignored and this script is the only thing that reads it — the value never
needs to pass through a chat session or shared terminal). A real API key, not
a short-lived OAuth token: the vault credential needs a static secret_value
it can hold and substitute on every request the sandbox makes to
api.anthropic.com.
"""

import json
import os
import sys
from pathlib import Path

import anthropic
import yaml

ROOT = Path(__file__).resolve().parent.parent
IDS_FILE = ROOT / "ids.json"
AGENT_YAML = ROOT / "agent.yaml"
ENV_FILE = ROOT / ".env"


def load_dotenv(path: Path) -> None:
    """Minimal .env loader — no extra dependency. Existing env vars win."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


def main():
    load_dotenv(ENV_FILE)

    if IDS_FILE.exists():
        print(f"{IDS_FILE} already exists — refusing to create duplicate resources.")
        print("To change the agent's behavior, edit agent.yaml and run:")
        print("  python scripts/update_agent.py")
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print(f"ANTHROPIC_API_KEY is not set (checked shell env and {ENV_FILE}).")
        print("The vault credential needs a real, long-lived API key (not an")
        print("`ant auth` OAuth session token) so it can be substituted into the")
        print("sandbox's outbound requests to api.anthropic.com on every eval run.")
        print(f"Either export it, or open {ENV_FILE} in an editor and set:")
        print("  ANTHROPIC_API_KEY=sk-ant-...")
        print("then re-run this script.")
        sys.exit(1)

    client = anthropic.Anthropic()

    print("Creating environment...")
    environment = client.beta.environments.create(
        name="skill-self-improver-env",
        config={
            "type": "cloud",
            "networking": {
                "type": "limited",
                "allowed_hosts": ["api.anthropic.com"],
                # Lets the sandbox `pip install anthropic` so the eval harness runs
                # against the real SDK instead of writing its own HTTPS shim when
                # PyPI is unreachable (observed in the first live run). Trade-off:
                # opens PyPI/npm/etc. egress in addition to api.anthropic.com — a
                # real, if small, widening of what the sandbox can reach.
                "allow_package_managers": True,
            },
        },
    )
    print(f"  environment_id = {environment.id}")

    print("Creating vault...")
    vault = client.beta.vaults.create(display_name="skill-self-improver")
    print(f"  vault_id = {vault.id}")

    print("Adding ANTHROPIC_API_KEY credential to vault...")
    client.beta.vaults.credentials.create(
        vault.id,
        display_name="Anthropic API key for eval harness",
        auth={
            "type": "environment_variable",
            "secret_name": "ANTHROPIC_API_KEY",
            "secret_value": api_key,
            "networking": {
                "type": "limited",
                "allowed_hosts": ["api.anthropic.com"],
            },
            "injection_location": {"header": True, "body": False},
        },
    )

    print("Creating agent from agent.yaml...")
    agent_config = yaml.safe_load(AGENT_YAML.read_text())
    agent = client.beta.agents.create(**agent_config)
    print(f"  agent_id = {agent.id} (version {agent.version})")

    IDS_FILE.write_text(json.dumps({
        "environment_id": environment.id,
        "vault_id": vault.id,
        "agent_id": agent.id,
        "agent_version": agent.version,
    }, indent=2))
    print(f"\nWrote {IDS_FILE}. Next: python scripts/launch_session.py")


if __name__ == "__main__":
    main()
