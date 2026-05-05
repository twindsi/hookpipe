# hookpipe

> Lightweight webhook relay with filtering and payload transformation rules

---

## Installation

```bash
pip install hookpipe
```

---

## Usage

Start a relay server that listens for incoming webhooks, applies transformation rules, and forwards them to a target URL.

**1. Define your rules in `rules.yaml`:**

```yaml
filters:
  - field: event
    equals: "push"

transform:
  - rename: repo.name -> repository
  - drop: sender.avatar_url

forward_to: "https://your-service.example.com/webhook"
```

**2. Run the relay:**

```bash
hookpipe serve --config rules.yaml --port 8080
```

**3. Point your webhook source to:**

```
http://localhost:8080/relay
```

Hookpipe will filter out non-matching events, reshape the payload according to your rules, and forward the result to the configured target.

---

## Programmatic API

```python
from hookpipe import Relay, RuleSet

rules = RuleSet.from_file("rules.yaml")
relay = Relay(rules=rules, target="https://your-service.example.com/webhook")
relay.serve(port=8080)
```

---

## License

[MIT](LICENSE)