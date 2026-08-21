# Week 4 Notes: Local AI with Ollama

**Ship:** Python script calls a local AI model and reliably returns valid JSON (summary, pain point, outreach line) from real lead data, with a validation layer.
**Stack this week:** Ollama, `requests`, `json`, `csv`, `os`, a Python virtual environment, Git.
**Status:** Complete. Pushed to github.com/farasatkhan1128/gtm-lab.

---

## 1. Concept cheat sheet

**Local model (Ollama) vs API model (Claude, ChatGPT)**
- Local runs on your own machine. After the one-time download it is free, works offline, and no lead data leaves your laptop. Bounded by your hardware.
- API runs on someone else's servers. Stronger reasoning, larger models, faster, more reliable at instruction-following. You pay per token and hit rate limits.
- Reach for local when privacy, marginal cost and high volume matter. Reach for the API when you need top-tier reasoning or reliability your hardware cannot provide.

**Ollama basics**
- Installs a background server at `http://localhost:11434`.
- `ollama pull <model>` downloads weights. `ollama run <model>` chats in the terminal. `/bye` exits.
- Talk to it from code with a `requests.post` to `/api/generate`.

**The response envelope**
- Ollama returns a JSON object, not just text. Key fields: `response` (the generated text), `done` and `done_reason` (finished cleanly), `eval_count` (tokens generated, the cost meter on a paid API), `context` (token IDs for memory across turns).

**`"stream": False`**
- Forces one complete JSON object instead of many newline-separated chunks. Without it, `response.json()` reliably breaks because the streamed body is not valid JSON as a whole.

**Temperature**
- Controls how predictable vs creative the output is, on a 0 to 1+ dial.
- Low (0.1 to 0.2) is focused and near-deterministic. High (0.8+) is varied and creative.
- Use low for GTM data extraction. High would add pointless variation and raise the risk of invented details.

**Structured JSON output, two forces**
- `format: "json"` guarantees the container is valid JSON syntax.
- The prompt fills the container correctly, defining which keys to produce and what goes in each.
- You need both. JSON mode alone can return valid but irrelevant keys. A good prompt alone can return the right idea wrapped in prose or broken JSON.

**The string trap**
- `data["response"]` arrives as a string that contains JSON. `json.loads()` converts that string into a real Python dict. Skip it and `result["summary"]` fails, because you cannot index a plain string by key.

**Virtual environment**
- One isolated Python plus its own packages, living in `.venv` inside the project.
- Fixes the three-versions muddle: activate it and `python` and `pip` always mean that one.
- A fresh venv is empty. Install libraries once, then lock with `pip freeze > requirements.txt`.
- Activate every new terminal: `.venv\Scripts\Activate.ps1`. Look for the `(.venv)` prefix.

---

## 2. Daily quizzes and answers

### Monday: install and first conversation

**Q1. Core trade-off, one advantage each.**
Local runs on your own machine for privacy and no per-request cost, but is limited by your hardware. API runs on powerful cloud servers with stronger models and speed, but you pay per use and send data out.

**Q2. Best interviewer answer for GTM or RevOps, local advantage.**
The main advantage of local is enriching sensitive prospect or CRM data without sending customer information to a third party. That improves privacy and, at high volume, cuts cost and sidesteps rate limits.

**Q3. Why the two models failed.**
First (llama3.1:8b): out of GPU memory (VRAM), too large to load. Second (llama3.2:3b): not a memory problem but a driver and build mismatch, a PTX JIT compilation failure where the packaged GPU code did not match the card.

**Q4. What `OLLAMA_LLM_LIBRARY=cpu` did.**
Forced Ollama to bypass the GPU and run entirely on the CPU, which avoided the driver problem and let the model start (slower but reliable).

**Q5. When an API is the better choice.**
When you need top-tier reasoning, complex extraction, high reliability and speed at scale that local hardware cannot match.

### Tuesday: call from Python, wrap in a function

**Q1. What the `ask_ollama()` function gives you.**
It turns the call into reusable code that takes a different prompt each time, instead of rewriting a hard-coded request. That is what lets Thursday loop over many accounts automatically.

**Q2. The two errors.**
`ModuleNotFoundError: No module named 'requests'`: the active environment did not have `requests`; installing it in that same venv fixed it. Old code running: the file was unsaved, so Python ran the old version on disk; saving fixed it.

**Q3. What `"stream": False` does.**
Tells Ollama to return one complete JSON object. Without it, the stream is many newline-separated chunks and `response.json()` reliably fails.

**Q4. Why return `data["response"].strip()` not `data`.**
The pipeline only needs the generated text, not metadata. Returning a clean string hides the plumbing so the caller does not need to know the envelope shape.

**Q5. Point of `timeout=120`, more so on CPU.**
`requests` has no default timeout, so without one a stuck request waits forever. Setting a generous cap matters more on CPU because local inference is slower and needs room, but the real reason is the default is "wait indefinitely."

### Wednesday: structured JSON and temperature

**Q1. Temperature, why 0.2 not 0.8.**
Temperature controls predictability vs creativity. 0.2 gives consistent, repeatable structure for enrichment. 0.8 would add variation and raise the hallucination risk.

**Q2. `format: "json"` vs the prompt.**
`format: "json"` controls syntax, forcing valid JSON. The prompt controls meaning and schema, which keys and what goes in each. Short version: format guarantees the container is valid, the prompt fills it correctly. With only JSON mode you can get valid but irrelevant fields. With only the prompt you can get the right content in prose or invalid JSON.

**Q3. What `json.loads()` does.**
Converts the JSON string in `data["response"]` into a real Python dict. Before that, Python sees one block of text, so `result["summary"]` cannot reach a named field.

**Q4. Why identical structure matters.**
It makes every result machine-readable and predictable, so the workflow can validate, filter, map and upload hundreds of accounts without custom handling per response.

**Q5. The nonexistent customer.**
That is a hallucination. Before using an outreach line, verify every company-specific claim against a trusted source, or automatically block any claim not supported by the input data.

### Thursday: enrich the real lead file

**Q1. `from structured import get_structured` and the guard.**
The import pulls the reusable function from `structured.py`. Tuesday's `if __name__ == "__main__":` guard stopped that file's test code from running on import, so only the function comes across.

**Q2. Why the original columns survived.**
Each row is a dict of the original columns. Adding new keys for the AI fields extends that same dict, so city, country and employees stay intact.

**Q3. What `try/except` prevents on 500 rows.**
It prevents one bad account, timeout or malformed response from crashing the whole run. The batch stays resilient: one failure cannot sink the other rows. A failed row keeps blank or flagged AI fields and processing continues.

**Q4. Why write to a new file.**
Writing to `companies_ai_enriched.csv` preserves the original dataset, so you can compare, rerun safely, debug and recover if output is poor.

**Q5. Three GTM stages and the Week 3 skill.**
Read or import lead data, then enrich and transform each account, then export the enriched dataset. The first and last stages run on Python CSV handling, specifically `csv.DictReader` (read) and `csv.DictWriter` (write).

### Friday: validation, retries, fallback

**Q1. When `validate()` rejects valid JSON.**
When the JSON parses and all keys exist but a value is blank. Valid JSON only proves the format is readable, not that the field is usable. A blank summary is useless to the pipeline, so reject it.

**Q2. Point of the retry, free locally.**
Gives the model another chance to produce a compliant result after a weak or malformed answer. Local inference only costs compute time; a paid API would charge for each extra request.

**Q3. Why `[NEEDS REVIEW]` beats a blank or a crash.**
It makes the failure visible and searchable while keeping the row. A blank could be mistaken for missing data. A crash would stop the rest of the file.

**Q4. Why `None` as the failure signal.**
`None` is a simple, expected "validation failed" signal. The caller checks `if result is not None` and retries or flags, without treating a routine quality failure as a system error.

**Q5. Why separate generate from validate.**
It lets you change, test and debug each responsibility on its own, so model output is never trusted just because it was produced.

---

## 3. Final Week 4 quiz and answers

**Q1. Local vs API, two-sentence version.**
Use a local Ollama model when privacy, control and low marginal cost matter, especially for high-volume enrichment on sensitive CRM data, since local avoids per-token cost and rate limits. Use an API model when you need stronger reasoning, higher reliability or faster performance than local hardware can provide.

**Q2. Temperature.**
It controls how predictable or creative the answers are. I used 0.2 because enrichment needs consistent, factual output. A high value would add pointless variation and raise the risk of hallucinated company details.

**Q3. Structured output.**
`format: "json"` forces valid JSON syntax (the container is valid). The prompt defines the schema and which fields to produce (the container is filled correctly). You need both, because JSON mode alone can return valid but irrelevant fields and the prompt alone can produce correct content in prose or malformed JSON.

**Q4. The string trap.**
`json.loads()` converts `data["response"]` from a JSON string into a Python dict. Without it, Python sees one block of text and `result["summary"]` fails.

**Q5. Validation, three layers in order.**
1. JSON parsing with `json.loads()`, which catches malformed JSON.
2. Schema checks, which confirm all required keys are present.
3. Value checks, which catch technically valid but unusable output such as blank or empty fields.

Note on scope: the current `validate()` catches malformed JSON, missing keys and blank values. It does not yet catch unsupported claims (hallucinations such as an invented customer name). That is a separate, harder layer, identified but not yet built. Know exactly where the safety net has holes.

**Q6. Full journey of one company.**
The script reads one row from `companies_enriched.csv`, keeping its existing fields such as city, country and employees. It builds a company-specific prompt, sends it to Ollama and parses the returned JSON string into a dict. The result passes through JSON parsing, schema and value validation, with retries if needed. The approved AI fields are appended to the original row and written to `companies_ai_enriched.csv`, or the row is marked `[NEEDS REVIEW]` if every attempt fails.

---

## 4. Debugging log (errors hit and fixes)

- **CUDA out of memory on llama3.1:8b.** GPU VRAM too small for an 8B model. Fix: pull a smaller model.
- **PTX JIT compilation failed on llama3.2:3b.** Driver and build mismatch, not memory. Fix: force CPU with the user env var `OLLAMA_LLM_LIBRARY=cpu`, quit Ollama from the tray, open a fresh terminal, rerun.
- **`.venv` did not exist.** The venv was never created, so scripts ran on system Python 3.13. Fix: `python -m venv .venv`, allow scripts once with `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, then `.venv\Scripts\Activate.ps1`.
- **`py` not recognised.** The Python launcher is not installed. Fix: use `python` instead of `py -3.12`. Isolation matters, not the exact version.
- **`No such file or directory` when running a script.** The terminal only looks in the folder you are standing in. Fix: `cd` into the week folder first. Quote folder names with spaces: `cd "W4 Local AI with Ollama"`.
- **`ModuleNotFoundError: No module named 'requests'`.** A fresh venv is empty. Fix: `pip install requests pandas`, then `pip freeze > requirements.txt`.
- **Script running old code after edits.** The file was unsaved; Python runs the version on disk. Fix: Ctrl+S, or turn on File, Auto Save.
- **`git status -` reported a clean tree wrongly.** A stray dash changed the command. Fix: run `git status` with no extra characters.

Quick tell: when the terminal output surprises you, stop and read it before acting.

---

## 5. Interview talking points

- Ran a model locally for privacy and cost, and can explain when the API is the better call (reasoning, reliability, rate limits at volume).
- Forced structured JSON at low temperature and can say why: format guarantees valid syntax, the prompt sets the schema, low temperature keeps output consistent for a pipeline.
- Built a validate, retry, fallback layer so raw model output never reaches a prospect unchecked. Caught a hallucination (an invented customer) and know that catching unsupported claims is a separate layer still to build.
- Tested the checking layer by feeding it hand-crafted bad strings, not by hoping the model would fail. Deterministic tests for a quality gate.
- Debugged real environment problems (GPU OOM, driver PTX failure, missing venv, path issues) and shipped anyway. Committed a clean, readable Git history, one labelled commit per week.

**One story to have ready:** "Tell me about something you built with AI." Walk through this pipeline end to end, including the hallucination you caught and why you do not let raw model output reach a prospect.
