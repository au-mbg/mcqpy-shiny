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

For Quarto embeds, use the Shinylive-specific snippet generator instead of importing
`mcqpy_shiny` directly inside the `.qmd` code block.

Generate a reusable snippet:

```bash
uv run python -m mcqpy_shiny.embed_cli \
  --output pages/_includes/example_quiz.qmd \
  --allow-manual-load \
  --title "MCQPy Quiz" \
  --card-width 900px
```

Then include it from a Quarto page:

```qmd
{{< include _includes/example_quiz.qmd >}}
```

Render or preview the Quarto project through `uv` so the `shinylive` CLI is on `PATH`:

```bash
cd pages
uv run quarto render
uv run quarto preview
```
