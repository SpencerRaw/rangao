# 燃稿 · FAQ

## Getting Started

### What do I need to run this?

- Python 3.10+
- A DeepSeek API key (or any OpenAI-compatible API)
- (Optional) WeChat Official Account AppID + AppSecret for auto-publish

### How much does it cost to run?

~¥0.3-0.5 per article via DeepSeek API (input + output tokens). The software itself is free and open-source (MIT).

### Can I use OpenAI instead of DeepSeek?

Yes. Set in `.env`:
```
RANGAO_LLM_BASE_URL=https://api.openai.com/v1
RANGAO_LLM_MODEL=gpt-4o
RANGAO_LLM_API_KEY=sk-your-openai-key
```

---

## Paper Download

### Why can't it download my paper?

The download chain tries three strategies in order:
1. **Sci-Hub** — works for most paywalled papers (check status: `--mirror-status`)
2. **Unpaywall** — finds open-access versions
3. **doi.org** — direct resolution (rarely works for paywalled papers)

If all fail, download the PDF manually and use `--pdf paper.pdf`.

### Is using Sci-Hub legal?

Sci-Hub operates in a legal gray area. 燃稿 is a tool — you are responsible for compliance with your local laws and institutional policies. The software provides the *capability* but does not encourage infringement.

### How do I add a new Sci-Hub mirror?

Edit `.env`:
```
RANGAO_SCIHUB_MIRROR=https://your-new-mirror.com
```
Or edit the `_DEFAULT_MIRRORS` list in `src/rangao/download/scihub.py`.

---

## Article Quality

### The article reads awkwardly. How do I fix it?

1. **Change the style template.** Try `--style academic_general` or create your own in `styles/`.
2. **Use the reasoning model.** Set `RANGAO_LLM_MODEL=deepseek-reasoner` for better logical flow (slower, more expensive).
3. **Adjust temperature.** Lower = more conservative/factual. Set `RANGAO_LLM_TEMPERATURE=0.3`.
4. **Edit the style YAML.** Each template has a `prompt:` field — this is injected directly into the LLM's system prompt. Tweak it.

### Can it write in English?

Yes. Create a style template with `language: en` and write the prompt in English. The LLM will follow.

### Does it hallucinate facts?

LLMs can hallucinate. 燃稿 mitigates this by:
- Providing the full paper text as context (not just the abstract)
- Requiring the model to cite figures and data from the paper
- Including DOI links in every article
- Low default temperature (0.7)

However, **always fact-check** before publishing — especially numerical values.

---

## WeChat Publishing

### Why do images not show up in WeChat?

WeChat blocks images hosted on unapproved domains. Solutions:
1. Use `--publish` to auto-upload to WeChat's own CDN
2. Manually upload images to WeChat's material library
3. The fallback CDNs (sm.ms, imgbb) *may* work depending on WeChat's current whitelist

### I get "IP not in whitelist" errors

WeChat requires your server's IP to be whitelisted. Options:
1. Log into WeChat backend → Settings → Security → IP Whitelist → add your IP
2. Use a VPS with a static IP (¥30-50/month)
3. If on dynamic IP, use ngrok or similar to get a fixed endpoint

### Can it publish directly (not just draft)?

WeChat's API does not allow fully automated publishing — articles must be reviewed and published by a human in the WeChat backend. 燃稿 pushes to the **draft box**, where you can review and publish with one click.

---

## Development

### How do I run tests?

```bash
pip install "rangao[test]"
python -m pytest tests/ -v
```

### How do I add a new feature?

1. Fork the repo
2. Create a branch
3. Add your code + tests
4. Submit a PR

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Where's the roadmap?

See [CHANGELOG.md](CHANGELOG.md#roadmap) and [PLAN.md](../PLAN.md).
