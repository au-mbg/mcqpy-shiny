# mcqpy-shiny

Minimal Py-Shiny quiz runner for browser-ready bundles exported by `mcqpy`.

## Python version

Use Python 3.13 for this package. Current `shiny` imports fail under Python 3.14 in this project setup, so create the environment with `uv` or `pixi` on 3.13 rather than 3.14.

## Bundle flow

1. Export a quiz bundle from an `mcqpy` project:

```bash
mcqpy export web -c config.yaml
```

2. Publish the generated directory containing:

```text
quiz.json
assets/
```

3. Run the generic app locally:

```bash
shiny run --reload src/mcqpy_shiny/app.py
```

For local development with `uv`, keep the dev dependencies installed:

```bash
uv sync
```

## Fixed quiz mode

For a locked Quarto/ShinyLive embed, create a tiny wrapper app:

```python
from mcqpy_shiny import create_app

app = create_app(
    fixed_url="https://example.github.io/course/quiz.json",
    allow_manual_load=False,
)
```

You can also hard-code a token instead of a URL:

```python
from mcqpy_shiny import create_app

app = create_app(
    fixed_token="mcqpy:...",
    allow_manual_load=False,
)
```

## Quarto / Shinylive embeds

There are now two embed modes:

- Supported: `source-embed`
- Experimental: `hosted-wheel`

For Quarto embeds, use the Shinylive-specific snippet generator instead of importing
`mcqpy_shiny` directly inside the `.qmd` code block.

Generate the supported source-embedded snippet:

```bash
uv run python -m mcqpy_shiny.embed_cli \
  --output pages/_includes/example_quiz.qmd \
  --mode source-embed \
  --allow-manual-load \
  --title "MCQPy Quiz" \
  --card-width 900px
```

Generate the experimental hosted-wheel snippet:

```bash
uv run python -m mcqpy_shiny.embed_cli \
  --output pages/_includes/hosted_wheel_quiz.qmd \
  --mode hosted-wheel \
  --wheel-url "https://<user>.github.io/<repo>/wheels/mcqpy_shiny-0.1.0-py3-none-any.whl" \
  --extra-requirement "shiny>=1.2.1" \
  --allow-manual-load \
  --title "MCQPy Quiz" \
  --card-width 900px
```

Then include one of those snippets from a Quarto page:

```qmd
{{< include _includes/example_quiz.qmd >}}
```

or:

```qmd
{{< include _includes/hosted_wheel_quiz.qmd >}}
```

The hosted-wheel mode is an experiment. Until it is proven reliable in the browser,
the supported path remains source embedding.

## Hosted wheel publishing

The repository includes a GitHub Pages workflow that builds a pure-Python wheel and
publishes a simple static wheel index. Once Pages is enabled for the repository, the
wheel becomes available at a full `.whl` URL that can be used with `--mode hosted-wheel`.

Render or preview the Quarto project through `uv` so the `shinylive` CLI is on `PATH`:

```bash
cd pages
uv run quarto render
uv run quarto preview
```
