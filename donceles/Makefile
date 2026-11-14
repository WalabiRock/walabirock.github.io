# Proyecto Donceles — todo se regenera desde params.json
PY ?= python3

.PHONY: pdf setup test review clean

pdf:            ## Regenera planos, gráficas, Excel y PDF, y corre todas las verificaciones
	$(PY) build.py

setup:          ## Instala dependencias
	$(PY) -m pip install -r requirements.txt

test:           ## Solo las pruebas (áreas, cronograma)
	$(PY) tests/test_areas.py && $(PY) tests/test_cronograma.py

review:         ## Aplica observaciones.csv, sube versión y reconstruye
	$(PY) apply_review.py

clean:
	rm -rf out build_tmp __pycache__
