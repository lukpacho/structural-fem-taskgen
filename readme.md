beam_project/
│
├── src/
│   ├── __init__.py
│   ├── generator.py
│   ├── geometry.py
│   ├── properties.py
│   ├── solver/
│   │   ├── __init__.py
│   │   ├── beam_solver.py  # Python-based solver to replace Octave functions
│   │
│   ├── pdf_generator/
│   │   ├── __init__.py
│   │   ├── latex_template.tex
│   │   ├── pdf_generator.py
│
├── data/
│   ├── results/
│   ├── temp/
│
├── tests/
│   ├── __init__.py
│   ├── test_generator.py
│   ├── test_solver.py
│
└── main.py
