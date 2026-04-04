# Geomancer

Geomancer is a local-first terminal chat tool that turns plain-English 3D model requests into Blender Python scripts. It sends your request to a local Ollama model, extracts valid `bpy` code, saves the script to `blender/generated_model.py`, and can optionally run that script in Blender.

Version 1 is intentionally simple:

- Terminal only
- Local Ollama backend
- Blender Python with `bpy`
- Beginner-friendly file layout
- Windows-friendly paths

## Project Structure

```text
geomancer/
  app/
    chat_agent.py
    llm_client.py
    blender_runner.py
    code_utils.py
    prompt_builder.py
    state.py
  blender/
    generated_model.py
    templates/
      base_rules.txt
    exports/
      stl/
  data/
    session_state.json
  tests/
    smoke_test.txt
  .env.example
  requirements.txt
  README.md
```

## What Geomancer Does

1. You type a modeling request in plain English.
2. Geomancer first asks Ollama for a small structured modeling plan.
3. Geomancer then sends that compact plan into a second Blender code-generation call.
4. Ollama returns text that should contain Blender Python code.
5. Geomancer extracts usable Python code.
6. The code is saved to `blender/generated_model.py`.
7. You can optionally run the generated script in Blender automatically.

## Requirements

- Windows
- Python 3.10 or newer
- Blender installed locally
- Ollama installed locally and running

## Install Python Dependencies

This version uses only the Python standard library.

```powershell
pip install -r requirements.txt
```

## Install Blender

1. Download Blender from the official site:
   `https://www.blender.org/download/`
2. Install it normally on Windows.
3. Check the path to `blender.exe`.

Default example path used by Geomancer:

```text
C:\Program Files\Blender Foundation\Blender 5.0\blender.exe
```

If your Blender path is different, copy `.env.example` to `.env` and update `BLENDER_PATH`.

## Set Blender Path

Create a `.env` file in the project root if you want Geomancer to use a specific Blender install path.

Example:

```text
BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe
```

## Blender Run Modes

- Background mode runs Blender with `--background --python blender/generated_model.py` and does not open the Blender UI.
- Interactive mode runs Blender with `--python blender/generated_model.py` and opens the Blender window.
- Interactive mode is recommended during development because you can see the generated result immediately.
- Interactive mode now launches Blender without blocking the terminal, so Geomancer returns immediately after opening the Blender UI.

## Install and Run Ollama

1. Download Ollama from:
   `https://ollama.com/download`
2. Install it on Windows.
3. Start Ollama.
4. Pull a local code model.

Example:

```powershell
ollama pull qwen2.5-coder:7b
```

You can also use another local model if it follows instructions well enough to output Blender Python.

## Pick a Model in Ollama

The default model is:

```text
qwen2.5-coder:7b
```

To change it:

1. Copy `.env.example` to `.env`
2. Edit the `OLLAMA_MODEL` value

Example:

```text
OLLAMA_MODEL=codellama:7b
```

The default Ollama API URL is:

```text
http://localhost:11434/api/generate
```

## Reducing Ollama Timeouts

- Shorter prompts usually return faster than long highly constrained prompts.
- Local coder models may take noticeably longer on CPU-heavy or lower-end systems.
- Preloading or warming the model can reduce cold-start delays before Geomancer sends a full request.
- Example warm-up command:

```powershell
ollama run qwen2.5-coder:7b ""
```

- Geomancer now sends `keep_alive` to Ollama to help reduce repeated cold-start delays.

## Optional `.env` Setup

Create a `.env` file in the project root if you want to override defaults:

```text
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5-coder:7b
BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe
```

## Run Geomancer

From the project root:

```powershell
python app/chat_agent.py
```

You will see:

```text
Geomancer>
```

Geomancer now shows lightweight terminal activity feedback during long local model generations so the terminal does not appear frozen while Ollama is working.

## Dev Console

Geomancer now includes a lightweight local Tkinter testing UI that keeps the terminal workflow intact.

Run it from the project root with:

```powershell
python app/dev_console.py
```

The Dev Console shows:

- a prompt input field
- a Run button
- a scrollable output log
- the current version
- the last parsed plan JSON
- the current generated script path

Terminal mode and GUI mode remain separate entry points, and both use the same local planning and template-generation flow.

## Commands

- `/help` shows the available commands
- `/quit` exits the program
- `/run` runs the last generated Blender script
- `/show` prints the current generated script
- `/save` saves a timestamped copy of the current script
- `/last` shows the last saved session info

## Example Workflow

Start the app:

```powershell
python app/chat_agent.py
```

Enter a request like:

```text
Create a 160mm UV sphere with a 90mm circular face opening and 3mm shell thickness.
```

Geomancer will then:

1. Build a compact planning prompt
2. Call Ollama locally for a JSON modeling plan
3. Build a shorter Blender code-generation prompt from that plan
4. Extract Blender Python code
5. Save the code to `blender/generated_model.py`
6. Ask whether to run the script in Blender

## Two-Stage Generation

Geomancer now uses a compact two-stage flow for local generation:

- Stage 1 asks Ollama for a compact JSON modeling plan.
- Stage 2 asks Ollama for Blender Python using that plan plus a very small built-in Blender rule summary.

This helps local models because the code-generation prompt is intentionally small and focused, which reduces hangs and timeouts compared with a large all-in-one prompt or a noisy grounded prompt.

- In template mode, Geomancer ignores noisy planner operation strings and builds the script only from normalized dimensions and flags such as `diameter_mm`, `shell_thickness_mm`, `front_opening_diameter_mm`, `flatten_bottom`, and `front_axis`.

## Second Test Example

Use this prompt for a stronger follow-up test:

```text
create a 160mm uv sphere, cut a 90mm circular face opening, and hollow it to 3mm shell thickness
```

## Current Modeling Constraints

- Geomancer currently produces rough primitive-based mechanical blockouts.
- Boolean cuts should be made with solid cutter objects such as cylinders or cubes, not flat curves.
- Boolean modifiers must live on the object being cut, not on the cutter object.
- Blender modifier application is context-sensitive, so the correct target object must be selected and set active before modifiers are applied.
- Front-opening cutters should be aligned on the intended front/back axis rather than the vertical axis.
- Cylinders default to Blender's Z axis and must be rotated for front/back cuts.
- Generated outputs may still need cleanup and refinement before they are ready for printing or final production use.

## Blender API Rule Library

Geomancer now uses a focused local Blender rule library in `blender/rules/` instead of treating all of `bpy` as fair game.

- `blender_api_rules.md` defines the conservative scene setup, modifier, transform, and safety rules.
- `allowed_operators.json` lists the small operator and modifier subset Geomancer should rely on for v1 blockouts.
- `banned_patterns.json` lists risky or unsupported patterns that will trigger a fallback script before saving.
- `modeling_conventions.md` maps plain-English requests like `front face opening` or `flatten the bottom` to fixed spatial behavior.

## Strict Blender Build Rules

Geomancer now uses a tiny allowlisted subset of `bpy` for rough blockout modeling instead of open-ended Blender code generation.

- Primitive creation is restricted to the allowlisted `bpy.ops.mesh` operators for UV spheres, cylinders, and cubes.
- Object creation should immediately capture `bpy.context.active_object` instead of guessing from operator return values.
- Boolean cutters must always be separate objects from the target object being cut.
- If generated code violates these strict rules, Geomancer falls back to a safe minimal script instead of saving risky code.

## Dimension Handling

- Geomancer should convert user-requested millimeter dimensions to Blender-safe meter values in generated scripts with a helper such as `def mm(value): return value / 1000.0`.
- Requested shell thickness values should be used directly, for example `3mm` should become `mm(3)` rather than a halved value.
- Front face openings should be cut with correctly placed solid cutter objects along the intended front-facing axis, not with arbitrary floating or flat geometry.

## Spatial Conventions

- Blender spatial directions are treated as `Z = up/down`, `Y = front/back`, and `X = left/right`.
- In Geomancer prompts, `front` means `+Y`, `back` means `-Y`, `top` means `+Z`, and `bottom` means `-Z`.
- This matters because cutters and flattening operations need consistent axis placement to create the intended geometry.

## First Runtime Test

1. Start Ollama and make sure your model is available:

```powershell
ollama run qwen2.5-coder:7b
```

2. In a new terminal, from the project root run:

```powershell
python app/chat_agent.py
```

3. At the `Geomancer>` prompt, enter:

```text
create a 160mm uv sphere and name it test_sphere
```

4. Inspect the generated script here:

```text
blender/generated_model.py
```

5. When prompted, optionally let Geomancer run Blender automatically.

## Where Generated Code Is Saved

The active generated Blender script is always saved here:

```text
blender/generated_model.py
```

Session state is saved here:

```text
data/session_state.json
```

## Notes for Beginners

- The generated script is plain Python that uses Blender's `bpy` module.
- If the model returns invalid output or no `bpy` usage is found, Geomancer saves a safe fallback Blender script.
- If Blender cannot be found, the app will show a readable error instead of crashing.
- If Ollama is not running, the app will show a readable connection error.
- Local model generation can occasionally take longer on more complex prompts, and shorter clearer prompts may perform better if timeouts occur.
- Geomancer shows simple terminal activity feedback during long model generations, but total generation time still depends on your hardware and prompt complexity.
- The first generated models are rough blockouts meant to get the shape started, not final print-ready parts.
- Millimeter-based shell thickness is still a rough blockout behavior and may need refinement for final print work.

## Debugging Failed Scripts

- If Blender shows a Python traceback, open `blender/generated_model.py` in Blender's Text Editor and run it there to inspect the exact error message.
- Geomancer currently targets rough primitive-based blockouts and a conservative subset of `bpy` to reduce Blender API hallucinations.
