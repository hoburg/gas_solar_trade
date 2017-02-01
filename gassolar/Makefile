all:
	python -c 'import gpkit.tools; exec gpkit.tools.mdmake("gassolarlat.md")'
	pandoc --template default.latex gassolarlat.md.tex.md -o "gassolarlat.pdf"
