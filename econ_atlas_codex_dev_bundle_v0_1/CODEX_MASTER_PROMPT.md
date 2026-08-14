# Master execution prompt

Implement the Argentina Economic Atlas frontend in this repository.

You are working from a frozen product/data contract, not inventing a new product.

Before coding:
1. read `AGENTS.md`;
2. read all files under `contracts/frontend/`;
3. inspect `fixtures/site-data/manifest.json`, `navigation.json`, and representative entity JSON;
4. inspect `reference/visual-target-inflation-topic.png`;
5. read `TECH_STACK.md`, `TARGET_REPO_LAYOUT.md`, and the active PR packet.

Target app location: `web/`.

Execute **PR-01 only unless the human explicitly authorizes subsequent packets**. Within PR-01 you may proceed
autonomously through routine work without intermediate confirmation. At the end, run every gate, report
exactly what changed and what remains, and stop for visual/human review.

The long-term end gate is a fully navigable static site for the one populated Nominal Stabilization slice
that visually resembles the supplied reference and renders all compiled public entities. Only three dummy
charts are implemented; every other Chart uses a polished generic placeholder.
