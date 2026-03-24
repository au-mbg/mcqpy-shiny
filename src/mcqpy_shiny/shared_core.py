"""Shared quiz UI/state for local and Shinylive runtimes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from html import escape

from shiny import App, reactive, render, ui

BundleLoader = Callable[[str], Awaitable[dict]]
TokenDecoder = Callable[[str], str]
BundleGrader = Callable[[dict, dict], dict]


def _answer_input_id(index: int) -> str:
    return f"answer_{index}"


def _choice_map(choices: list[str]) -> dict[str, str]:
    return {
        chr(65 + index): f"({chr(65 + index)}) {choice}"
        for index, choice in enumerate(choices)
    }


def _render_question_media(question: dict) -> list:
    media = []
    captions = question.get("image_captions", {})

    for index, image in enumerate(question.get("images", [])):
        media.append(ui.img(src=image, style="max-width: 100%; height: auto;"))
        caption = captions.get(str(index), captions.get(index))
        if caption:
            media.append(ui.p(caption, class_="text-muted"))

    shared_caption = captions.get("-1", captions.get(-1))
    if shared_caption:
        media.append(ui.p(shared_caption, class_="text-muted"))

    for block in question.get("code_blocks", []):
        media.append(
            ui.tags.pre(
                ui.tags.code(
                    block.get("code", ""),
                    **{"data-language": block.get("language") or "text"},
                )
            )
        )
    return media


def _question_answer_ui(question: dict, index: int):
    input_id = _answer_input_id(index)
    choices = _choice_map(question["choices"])
    if question["question_type"] == "single":
        return ui.input_radio_buttons(input_id, "Select your answer", choices=choices)
    return ui.input_checkbox_group(input_id, "Select your answers", choices=choices)


def _result_chart_svg(questions: list[dict], graded: dict) -> ui.HTML:
    width = 760
    row_height = 30
    top = 28
    left = 92
    right = 58
    bottom = 36
    plot_width = width - left - right
    height = top + bottom + row_height * max(len(graded["question_results"]), 1)
    max_points = max((item["max_points"] for item in graded["question_results"]), default=1)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="auto" role="img" aria-label="Points by question">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#ffffff"/>',
        f'<line x1="{left}" y1="{top - 8}" x2="{left}" y2="{height - bottom + 4}" stroke="#c9d2dc" stroke-width="1"/>',
    ]

    for idx, (question, item) in enumerate(zip(questions, graded["question_results"], strict=False)):
        y = top + idx * row_height
        bar_width = 0 if max_points == 0 else (item["points"] / max_points) * plot_width
        max_width = 0 if max_points == 0 else (item["max_points"] / max_points) * plot_width
        label = escape(str(idx + 1))
        title = escape(question["slug"])

        parts.extend(
            [
                f'<title>{title}</title>',
                f'<text x="{left - 10}" y="{y + 17}" text-anchor="end" font-size="13" fill="#334155">{label}</text>',
                f'<rect x="{left}" y="{y + 4}" rx="6" ry="6" width="{max_width}" height="18" fill="#e9eef4"/>',
                f'<rect x="{left}" y="{y + 4}" rx="6" ry="6" width="{bar_width}" height="18" fill="#3b82f6"/>',
                f'<text x="{left + max_width + 8}" y="{y + 18}" font-size="12" fill="#475569">{item["points"]}/{item["max_points"]}</text>',
            ]
        )

    for tick in range(max_points + 1):
        x = left + (0 if max_points == 0 else (tick / max_points) * plot_width)
        parts.extend(
            [
                f'<line x1="{x}" y1="{top - 8}" x2="{x}" y2="{height - bottom + 4}" stroke="#f1f5f9" stroke-width="1"/>',
                f'<text x="{x}" y="{height - 10}" text-anchor="middle" font-size="12" fill="#64748b">{tick}</text>',
            ]
        )

    parts.append("</svg>")
    return ui.HTML("".join(parts))


def _question_overview_grid(questions: list[dict], answers: dict, current_index: int):
    buttons = []
    for idx, question in enumerate(questions):
        saved = answers.get(question["qid"])
        is_answered = saved not in (None, [], ())
        classes = ["mcqpy-overview-button"]
        if is_answered:
            classes.append("is-answered")
        if idx == current_index:
            classes.append("is-current")

        buttons.append(
            ui.tags.button(
                ui.tags.span(str(idx + 1), class_="mcqpy-overview-number"),
                type="button",
                onclick=f"Shiny.setInputValue('jump_grid', {idx + 1}, {{priority: 'event'}})",
                class_=" ".join(classes),
                title=question["slug"],
            )
        )

    return ui.div(*buttons, class_="mcqpy-overview-grid")


def _build_css(card_width: str) -> str:
    return """
.mcqpy-shell {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 1rem 3rem;
}
.mcqpy-card {
  width: __CARD_WIDTH__;
  max-width: __CARD_WIDTH__;
  min-width: __CARD_WIDTH__;
  margin: 0 auto;
  box-sizing: border-box;
  overflow-x: hidden;
}
.mcqpy-card .card-body {
  overflow-x: hidden;
}
.mcqpy-question-text,
.mcqpy-question-text p,
.mcqpy-question-text li {
  font-size: 1.05rem;
  line-height: 1.65;
  overflow-wrap: anywhere;
  word-break: break-word;
}
.mcqpy-question-meta {
  margin: 0.25rem 0 1rem;
  color: #475569;
  font-size: 0.98rem;
}
.mcqpy-media {
  margin: 1rem 0 1.5rem;
  min-height: 0;
}
.mcqpy-media img {
  display: block;
  max-width: min(100%, 900px);
  height: auto;
  margin: 0 auto;
}
.mcqpy-media pre {
  max-width: 100%;
  overflow-x: auto;
  white-space: pre-wrap;
}
.mcqpy-media code,
.mcqpy-question-text code {
  overflow-wrap: anywhere;
  word-break: break-word;
}
.mcqpy-answer-group .shiny-input-radiogroup,
.mcqpy-answer-group .shiny-input-checkboxgroup {
  width: 100%;
}
.mcqpy-answer-group .radio,
.mcqpy-answer-group .checkbox {
  display: block;
  width: 100%;
  margin-bottom: 0.9rem;
}
.mcqpy-answer-group label.radio,
.mcqpy-answer-group label.checkbox {
  display: block;
  width: 100%;
  padding: 0.9rem 1rem;
  border: 1px solid #d9dee5;
  border-radius: 0.75rem;
  background: #fff;
}
.mcqpy-answer-group input[type="radio"],
.mcqpy-answer-group input[type="checkbox"] {
  margin-right: 0.65rem;
}
.mcqpy-nav-row {
  margin-top: 1.25rem;
}
.mcqpy-jump-row {
  margin: 0.5rem 0 1rem;
  align-items: end;
}
.mcqpy-results-chart {
  margin: 1.25rem 0 0.75rem;
  padding: 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.85rem;
  background: #fcfdff;
}
.mcqpy-results-chart svg {
  display: block;
  width: 100%;
  height: auto;
}
.mcqpy-overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(68px, 1fr));
  gap: 0.6rem;
  margin: 0.9rem 0 1.25rem;
}
.mcqpy-overview-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 58px;
  padding: 0.7rem;
  border: 1px solid #d9dee5;
  border-radius: 0.75rem;
  background: #fff;
  text-align: center;
}
.mcqpy-overview-button.is-answered {
  background: #eff6ff;
  border-color: #93c5fd;
}
.mcqpy-overview-button.is-current {
  border-color: #2563eb;
  box-shadow: inset 0 0 0 1px #2563eb;
}
.mcqpy-overview-number {
  font-size: 1rem;
  font-weight: 700;
  color: #2563eb;
}
@media (max-width: 820px) {
  .mcqpy-card {
    width: 100%;
    max-width: 100%;
    min-width: 0;
  }
}
""".replace("__CARD_WIDTH__", card_width)


MATHJAX_HEAD = """
window.MathJax = {
  tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']], displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']] },
  svg: { fontCache: 'global' }
};
"""

MATHJAX_BOOTSTRAP = """
(() => {
  let timer = null;
  let observer = null;
  const typeset = () => {
    if (!window.MathJax || !window.MathJax.typesetPromise) return;
    const nodes = document.querySelectorAll('.mcqpy-math');
    if (nodes.length) window.MathJax.typesetPromise(Array.from(nodes)).catch(() => {});
  };
  const schedule = () => {
    clearTimeout(timer);
    timer = setTimeout(typeset, 125);
  };
  const install = () => {
    schedule();
    if (observer || !document.body) return;
    observer = new MutationObserver(schedule);
    observer.observe(document.body, { childList: true, subtree: true });
  };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', install, { once: true });
  } else {
    install();
  }
  window.addEventListener('load', schedule);
})();
"""


def create_quiz_app(
    *,
    load_bundle: BundleLoader,
    decode_token: TokenDecoder,
    grade_bundle: BundleGrader,
    missing_bundle_message: str,
    fixed_url: str | None = None,
    fixed_token: str | None = None,
    allow_manual_load: bool = True,
    title: str = "MCQPy Quiz",
    card_width: str = "900px",
) -> App:
    app_ui = ui.page_fillable(
        ui.head_content(
            ui.tags.script(MATHJAX_HEAD),
            ui.tags.script(src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"),
            ui.tags.style(_build_css(card_width)),
            ui.tags.script(MATHJAX_BOOTSTRAP),
        ),
        ui.div(
            ui.h1(title),
            ui.output_ui("load_panel"),
            ui.hr(),
            ui.output_ui("content"),
            class_="mcqpy-shell",
        ),
    )

    def server(input, output, session):
        bundle = reactive.value(None)
        answers = reactive.value({})
        current_index = reactive.value(0)
        load_error = reactive.value(None)
        result = reactive.value(None)
        auto_loaded = reactive.value(False)

        def _bundle() -> dict | None:
            return bundle.get()

        def _current_questions() -> list[dict]:
            loaded = _bundle()
            return [] if loaded is None else loaded["questions"]

        def _store_current_answer() -> None:
            loaded = _bundle()
            if loaded is None:
                return

            index = current_index.get()
            questions = loaded["questions"]
            if not (0 <= index < len(questions)):
                return

            input_id = _answer_input_id(index)
            current_value = input[input_id]()
            next_answers = dict(answers.get())
            next_answers[questions[index]["qid"]] = current_value
            answers.set(next_answers)

        async def _load_source(source: str) -> None:
            if not source:
                load_error.set("Provide a quiz bundle URL, token, or local path.")
                return

            try:
                loaded = await load_bundle(source)
            except Exception as exc:
                load_error.set(str(exc))
                bundle.set(None)
                result.set(None)
                return

            load_error.set(None)
            bundle.set(loaded)
            answers.set({})
            result.set(None)
            current_index.set(0)

        @reactive.effect
        async def _auto_load_fixed_bundle():
            if auto_loaded.get():
                return

            source = None
            if fixed_token:
                source = decode_token(fixed_token)
            elif fixed_url:
                source = fixed_url

            if source is None:
                return

            auto_loaded.set(True)
            await _load_source(source)

        @reactive.effect
        @reactive.event(input.load_link)
        async def _load_link():
            await _load_source(input.quiz_url().strip())

        @reactive.effect
        @reactive.event(input.load_token)
        async def _load_token():
            token = input.quiz_token().strip()
            try:
                source = decode_token(token)
            except ValueError as exc:
                load_error.set(str(exc))
                return
            await _load_source(source)

        @reactive.effect
        @reactive.event(input.next_question)
        def _next_question():
            _store_current_answer()
            questions = _current_questions()
            if questions:
                current_index.set(min(len(questions), current_index.get() + 1))

        @reactive.effect
        @reactive.event(input.prev_question)
        def _prev_question():
            _store_current_answer()
            current_index.set(max(0, current_index.get() - 1))

        @reactive.effect
        @reactive.event(input.jump_slider)
        def _jump_from_slider():
            loaded = _bundle()
            if loaded is None:
                return
            _store_current_answer()
            target = input.jump_slider()
            if target is None:
                return
            current_index.set(min(max(target - 1, 0), len(loaded["questions"])))

        @reactive.effect
        @reactive.event(input.jump_number)
        def _jump_from_number():
            loaded = _bundle()
            if loaded is None:
                return
            _store_current_answer()
            target = input.jump_number()
            if target is None:
                return
            current_index.set(min(max(target - 1, 0), len(loaded["questions"])))

        @reactive.effect
        @reactive.event(input.jump_grid)
        def _jump_from_grid():
            loaded = _bundle()
            if loaded is None:
                return
            _store_current_answer()
            target = input.jump_grid()
            if target is None:
                return
            current_index.set(min(max(int(target) - 1, 0), len(loaded["questions"])))

        @reactive.effect
        @reactive.event(input.submit_quiz)
        def _submit_quiz():
            loaded = _bundle()
            if loaded is None:
                return
            _store_current_answer()
            result.set(grade_bundle(loaded, answers.get()))

        @reactive.effect
        @reactive.event(input.restart_quiz)
        def _restart_quiz():
            answers.set({})
            result.set(None)
            current_index.set(0)

        @output
        @render.ui
        def load_panel():
            if _bundle() is not None:
                return ui.div()

            if fixed_url or fixed_token:
                if not allow_manual_load:
                    return ui.div()
                helper = "A fixed quiz is configured for this app, or you can load another one."
            else:
                helper = "Load a quiz bundle from a public link or an obfuscated token."

            return ui.card(
                ui.p(helper),
                ui.row(
                    ui.column(
                        6,
                        ui.input_text("quiz_url", "Quiz bundle URL", placeholder="https://.../quiz.json"),
                        ui.input_action_button("load_link", "Load from link"),
                    ),
                    ui.column(
                        6,
                        ui.input_text("quiz_token", "Obfuscated token", placeholder="mcqpy:..."),
                        ui.input_action_button("load_token", "Load from token"),
                    ),
                ),
                class_="mcqpy-card",
            )

        @output
        @render.ui
        def content():
            if load_error.get():
                return ui.p(load_error.get(), class_="text-danger")

            loaded = _bundle()
            if loaded is None:
                return ui.markdown(missing_bundle_message)

            if result.get() is not None:
                graded = result.get()
                summary = [
                    ui.h2("Results"),
                    ui.p(f"Score: {graded['points']} / {graded['max_points']}"),
                    ui.div(
                        ui.h3("Points by question"),
                        _result_chart_svg(loaded["questions"], graded),
                        ui.p(
                            "Bars show earned points for each question number; hover labels reflect the full slug.",
                            class_="text-muted",
                        ),
                        class_="mcqpy-results-chart",
                    ),
                    ui.tags.ul(
                        *[
                            ui.tags.li(
                                f"{question['slug']}: {item['points']}/{item['max_points']}"
                            )
                            for question, item in zip(
                                loaded["questions"], graded["question_results"], strict=False
                            )
                        ]
                    ),
                    ui.input_action_button("restart_quiz", "Restart quiz"),
                ]
                return ui.card(*summary, class_="mcqpy-card")

            questions = loaded["questions"]
            index = current_index.get()

            if index >= len(questions):
                items = []
                for question in questions:
                    saved = answers.get().get(question["qid"])
                    items.append(
                        ui.tags.li(
                            f"{question['slug']}: {saved if saved not in (None, [], ()) else 'No answer selected'}"
                        )
                    )

                return ui.card(
                    ui.h2("Review"),
                    ui.p("Submit the quiz when you are ready."),
                    _question_overview_grid(questions, answers.get(), index),
                    ui.tags.ul(*items),
                    ui.row(
                        ui.column(6, ui.input_action_button("prev_question", "Previous question")),
                        ui.column(6, ui.input_action_button("submit_quiz", "Submit and grade")),
                    ),
                    class_="mcqpy-card mcqpy-math",
                )

            question = questions[index]
            progress = f"Question {index + 1} of {len(questions)}"
            question_kind = (
                "Single answer" if question["question_type"] == "single" else "Multiple answers"
            )

            body = [
                ui.h2(loaded.get("metadata", {}).get("title", title)),
                ui.p(progress, class_="text-muted"),
                ui.row(
                    ui.column(
                        8,
                        ui.input_slider(
                            "jump_slider",
                            "Jump to question",
                            min=1,
                            max=len(questions) + 1,
                            value=index + 1,
                            step=1,
                            width="100%",
                        ),
                    ),
                    ui.column(
                        4,
                        ui.input_numeric(
                            "jump_number",
                            "Question number",
                            value=index + 1,
                            min=1,
                            max=len(questions) + 1,
                            width="100%",
                        ),
                    ),
                    class_="mcqpy-jump-row",
                ),
                ui.h3(question["slug"]),
                ui.p(
                    f"{question_kind} • {question['point_value']} point"
                    f"{'' if question['point_value'] == 1 else 's'}",
                    class_="mcqpy-question-meta",
                ),
                ui.div(ui.markdown(question["text"]), class_="mcqpy-question-text"),
                ui.div(*_render_question_media(question), class_="mcqpy-media"),
                ui.div(_question_answer_ui(question, index), class_="mcqpy-answer-group"),
                ui.row(
                    ui.column(4, ui.input_action_button("prev_question", "Previous")),
                    ui.column(4, ui.input_action_button("next_question", "Next")),
                    ui.column(4, ui.div()),
                    class_="mcqpy-nav-row",
                ),
                _question_overview_grid(questions, answers.get(), index),
            ]
            return ui.card(*body, class_="mcqpy-card mcqpy-math")

    return App(app_ui, server)
