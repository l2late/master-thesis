from pathlib import Path


def latex_table_to_image(latex_content, output_path, dpi=300):
    """Convert LaTeX table to PNG image."""
    import subprocess
    import tempfile

    # Create standalone document
    if "\\begin{document}" in latex_content:
        # Content is already a complete document, use as-is
        standalone_tex = latex_content
    else:
        # Wrap table in standalone document
        standalone_tex = f"""\\documentclass[preview,border=2mm]{{standalone}}
        \\usepackage{{booktabs}}
        \\usepackage{{amssymb}}
        \\usepackage{{varwidth}}
        \\begin{{document}}
        \\begin{{varwidth}}{{\\linewidth}}
        {latex_content}
        \\end{{varwidth}}
        \\end{{document}}
        """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        tex_file = tmpdir / "table.tex"

        # Write tex file
        tex_file.write_text(standalone_tex)

        # Compile to PDF
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", tex_file.name],
            cwd=tmpdir,
            capture_output=True,
        )

        # Check if PDF was created
        pdf_file = tmpdir / "table.pdf"
        if not pdf_file.exists():
            print("Error: PDF compilation failed")
            print(result.stdout.decode())
            return

        # Check page count for debugging
        print(
            f"PDF info: {subprocess.run(['pdfinfo', str(pdf_file)], capture_output=True, text=True).stdout}"
        )

        subprocess.run(
            [
                "magick",
                "-density",
                str(dpi),
                str(pdf_file),  # REMOVED [0] to read all pages
                "-background",
                "white",
                "-alpha",
                "remove",
                "-alpha",
                "off",
                "-append",  # ADDED to stack pages vertically
                "-trim",
                str(output_path),
            ],
            check=True,
        )

    print(f"✓ Generated: {output_path}")


if __name__ == "__main__":
    # Usage:
    from alphabuilding.utils.paths import paths

    root_dir = paths.root_dir

    # latex_content = root_dir / "tables/val_rmse_comparison.tex"
    latex_content = root_dir / "output/results_table.tex"
    latex_content = latex_content.read_text()
    output_path = paths.output_dir / "results_table.png"
    latex_table_to_image(latex_content, str(output_path))
