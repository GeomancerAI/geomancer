"""Helpers for running Blender with a generated Python script."""

from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Update this path if Blender is installed somewhere else on your system.
DEFAULT_BLENDER_PATH = r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"


def load_dotenv_values() -> dict[str, str]:
    """Load simple KEY=VALUE pairs from a local .env file if it exists."""
    values: dict[str, str] = {}

    if not ENV_FILE_PATH.exists():
        return values

    for raw_line in ENV_FILE_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


def get_blender_path() -> Path:
    """Resolve Blender's executable path from env vars or the default example."""
    env_values = load_dotenv_values()
    configured_path = os.getenv("BLENDER_PATH") or env_values.get("BLENDER_PATH") or DEFAULT_BLENDER_PATH
    return Path(configured_path)


def run_generated_script(script_path: Path, interactive: bool = True) -> tuple[bool, str]:
    """Run Blender and execute the given Python script."""
    blender_path = get_blender_path()
    script_path = Path(script_path)
    mode_text = "interactive" if interactive else "background"
    print(f"Using Blender path: {blender_path}")
    print(f"Using Blender mode: {mode_text}")

    if not blender_path.exists():
        return False, (
            f"Blender was not found at: {blender_path}. "
            "Create or update a .env file in the project root with "
            r"BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
        )

    if not script_path.exists():
        return False, f"Generated script not found at: {script_path}"

    command = [str(blender_path)]
    if not interactive:
        command.append("--background")
    command.extend(["--python", str(script_path)])

    try:
        if interactive:
            process = subprocess.Popen(command)
            print("Blender launched in interactive mode. Close Blender to return to Geomancer.")
            return_code = process.wait()
            if return_code != 0:
                return False, f"Blender exited with code {return_code} in interactive mode."
            return True, "Blender session ended."

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False, f"Blender run failed after timing out at 300 seconds. Script: {script_path}"
    except OSError as error:
        return False, f"Blender could not be started from {blender_path}. Details: {error}"

    if result.returncode != 0:
        stderr_text = result.stderr.strip() or "No stderr output was returned."
        return False, (
            f"Blender failed with exit code {result.returncode} while running {script_path}. "
            f"Details: {stderr_text}"
        )

    return True, f"Blender completed successfully in {mode_text} mode using {blender_path}."


def open_generated_model_file(model_path: Path, interactive: bool = True) -> tuple[bool, str]:
    """Open a persisted model artifact directly in Blender."""
    blender_path = get_blender_path()
    model_path = Path(model_path)
    mode_text = "interactive" if interactive else "background"
    print(f"Using Blender path: {blender_path}")
    print(f"Using Blender mode: {mode_text}")

    if not blender_path.exists():
        return False, (
            f"Blender was not found at: {blender_path}. "
            "Create or update a .env file in the project root with "
            r"BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
        )

    if not model_path.exists():
        return False, f"Model artifact not found at: {model_path}"

    command = [str(blender_path)]
    if not interactive:
        command.append("--background")
    temp_script_path: Path | None = None
    if model_path.suffix.lower() in {".glb", ".gltf"}:
        wrapper_text = textwrap.dedent(
            f"""
            import traceback

            MODEL_PATH = {str(model_path)!r}

            try:
                import bpy
                import addon_utils

                addon_utils.enable("io_scene_gltf2", default_set=True, persistent=True)
                bpy.ops.object.select_all(action='SELECT')
                bpy.ops.object.delete(use_global=False)
                bpy.ops.import_scene.gltf(filepath=MODEL_PATH)
                print("Imported model artifact:", MODEL_PATH)
            except Exception:
                traceback.print_exc()
                raise
            """
        ).strip()
        with tempfile.NamedTemporaryFile("w", suffix="_geomancer_model_open.py", delete=False, encoding="utf-8") as handle:
            handle.write(wrapper_text)
            temp_script_path = Path(handle.name)
        command.extend(["--python", str(temp_script_path)])
    else:
        command.append(str(model_path))

    try:
        if interactive:
            process = subprocess.Popen(command)
            print("Blender launched in interactive mode with a model artifact. Close Blender to return to Geomancer.")
            return_code = process.wait()
            if return_code != 0:
                return False, f"Blender exited with code {return_code} while opening {model_path}."
            return True, "Blender session ended."

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False, f"Blender model open timed out after 300 seconds for artifact: {model_path}"
    except OSError as error:
        return False, f"Blender could not be started from {blender_path}. Details: {error}"
    finally:
        if temp_script_path is not None:
            temp_script_path.unlink(missing_ok=True)

    if result.returncode != 0:
        stderr_text = result.stderr.strip() or "No stderr output was returned."
        return False, (
            f"Blender failed with exit code {result.returncode} while opening {model_path}. "
            f"Details: {stderr_text}"
        )

    return True, f"Blender completed successfully in {mode_text} mode using {blender_path}."


def export_preview_model(script_path: Path, preview_path: Path, export_format: str = "GLB") -> tuple[bool, str]:
    """Run Blender headlessly and export a preview model for the desktop viewer."""
    blender_path = get_blender_path()
    script_path = Path(script_path)
    preview_path = Path(preview_path)

    if not blender_path.exists():
        return False, (
            f"Blender was not found at: {blender_path}. "
            "Create or update a .env file in the project root with "
            r"BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
        )

    if not script_path.exists():
        return False, f"Generated script not found at: {script_path}"

    preview_path.parent.mkdir(parents=True, exist_ok=True)

    wrapper_text = textwrap.dedent(
        f"""
        import os
        import runpy
        import traceback

        import bpy

        SCRIPT_PATH = {str(script_path)!r}
        PREVIEW_PATH = {str(preview_path)!r}

        try:
            runpy.run_path(SCRIPT_PATH, run_name="__main__")
            target = bpy.data.objects.get("Geomancer_Final")
            if target is None:
                raise RuntimeError("Geomancer_Final was not found after running the generated script.")
            bpy.ops.object.select_all(action='DESELECT')
            target.select_set(True)
            bpy.context.view_layer.objects.active = target
            bpy.ops.export_scene.gltf(
                filepath=PREVIEW_PATH,
                export_format={export_format!r},
                use_selection=True,
                export_yup=True,
            )
            print(f"Preview export complete: {{PREVIEW_PATH}}")
        except Exception:
            traceback.print_exc()
            raise
        """
    ).strip()

    temp_script_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix="_geomancer_preview_export.py", delete=False, encoding="utf-8") as handle:
            handle.write(wrapper_text)
            temp_script_path = Path(handle.name)

        command = [
            str(blender_path),
            "--background",
            "--factory-startup",
            "--python",
            str(temp_script_path),
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False, f"Preview export timed out after 300 seconds for script: {script_path}"
    except OSError as error:
        return False, f"Blender could not be started from {blender_path}. Details: {error}"
    finally:
        if temp_script_path is not None:
            temp_script_path.unlink(missing_ok=True)

    if result.returncode != 0:
        stderr_text = result.stderr.strip() or result.stdout.strip() or "No export output was returned."
        return False, (
            f"Preview export failed with exit code {result.returncode} while running {script_path}. "
            f"Details: {stderr_text}"
        )

    if not preview_path.exists():
        return False, f"Preview export completed without writing a file to: {preview_path}"

    return True, f"Preview exported successfully to {preview_path}."


def export_model_to_stl(source_path: Path, stl_path: Path) -> tuple[bool, str]:
    """Export the current final model artifact to STL through Blender."""
    blender_path = get_blender_path()
    source_path = Path(source_path)
    stl_path = Path(stl_path)

    if not blender_path.exists():
        return False, (
            f"Blender was not found at: {blender_path}. "
            "Create or update a .env file in the project root with "
            r"BLENDER_PATH=C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"
        )

    if not source_path.exists():
        return False, f"Source model artifact not found at: {source_path}"

    stl_path.parent.mkdir(parents=True, exist_ok=True)
    wrapper_text = textwrap.dedent(
        f"""
        import addon_utils
        import runpy
        import traceback

        import bpy

        SOURCE_PATH = {str(source_path)!r}
        STL_PATH = {str(stl_path)!r}

        try:
            bpy.ops.wm.read_factory_settings(use_empty=True)
            if SOURCE_PATH.lower().endswith((".glb", ".gltf")):
                addon_utils.enable("io_scene_gltf2", default_set=True, persistent=True)
                bpy.ops.import_scene.gltf(filepath=SOURCE_PATH)
            elif SOURCE_PATH.lower().endswith(".py"):
                runpy.run_path(SOURCE_PATH, run_name="__main__")
            else:
                raise RuntimeError(f"Unsupported source artifact format for STL export: {{SOURCE_PATH}}")

            mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
            if not mesh_objects:
                raise RuntimeError("No mesh objects were available for STL export.")

            bpy.ops.object.select_all(action='DESELECT')
            for obj in mesh_objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = mesh_objects[0]

            if hasattr(bpy.ops.wm, "stl_export"):
                bpy.ops.wm.stl_export(filepath=STL_PATH, export_selected_objects=True)
            elif hasattr(bpy.ops.export_mesh, "stl"):
                bpy.ops.export_mesh.stl(filepath=STL_PATH, use_selection=True)
            else:
                raise RuntimeError("No STL export operator is available in this Blender build.")

            print(f"STL export complete: {{STL_PATH}}")
        except Exception:
            traceback.print_exc()
            raise
        """
    ).strip()

    temp_script_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", suffix="_geomancer_stl_export.py", delete=False, encoding="utf-8") as handle:
            handle.write(wrapper_text)
            temp_script_path = Path(handle.name)

        command = [
            str(blender_path),
            "--background",
            "--factory-startup",
            "--python",
            str(temp_script_path),
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return False, f"STL export timed out after 300 seconds for source artifact: {source_path}"
    except OSError as error:
        return False, f"Blender could not be started from {blender_path}. Details: {error}"
    finally:
        if temp_script_path is not None:
            temp_script_path.unlink(missing_ok=True)

    if result.returncode != 0:
        stderr_text = result.stderr.strip() or result.stdout.strip() or "No export output was returned."
        return False, (
            f"STL export failed with exit code {result.returncode} while running {source_path}. "
            f"Details: {stderr_text}"
        )

    if not stl_path.exists():
        return False, f"STL export completed without writing a file to: {stl_path}"

    return True, f"STL exported successfully to {stl_path}."
