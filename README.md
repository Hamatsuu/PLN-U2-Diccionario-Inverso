Diccionario inverso

Requiere Python 3.13. Abre una terminal dentro de la carpeta entregable_final,
donde está pyproject.toml, e instala las dependencias:

    uv venv --python 3.13
    uv pip install --python .venv -r requirements.txt

La primera instalación necesita internet. Los datos y los vectores ya vienen incluidos.

Consultas

    .venv/bin/python -m diccionario_inverso

Elige grafo, modelo y número de resultados. Con Enter se usan NAP, PageRank y cinco
candidatos. Después escribe descripciones; /menu cambia la configuración y /salir
termina. Las consultas no entrenan modelos ni evalúan corpus. node2vec usa los vectores
guardados. Para una consulta directa:

    .venv/bin/python -m diccionario_inverso --consulta "objeto que sirve para cortar papel"

Resultados

Instala el kernel y abre JupyterLab:

    .venv/bin/python -m ipykernel install --prefix=.venv --name diccionario-inverso
    .venv/bin/python -m jupyterlab

Abre resultados.ipynb y selecciona el kernel diccionario-inverso. El notebook lee las
ejecuciones guardadas en resultados/. No vuelve a entrenar ni a evaluar la prueba por defecto.

experimentacion.ipynb es el notebook original de la práctica. Está pensado para Google Colab
y Google Drive, con rutas en /content/gdrive. Para ejecutarlo fuera de Colab habría que
cambiar esas rutas.

Experimentos explícitos

    .venv/bin/python -m diccionario_inverso --listar
    .venv/bin/python -m diccionario_inverso --config configuraciones/ejemplo.json

Una ejecución guardada no se sobrescribe. El código está en src/diccionario_inverso,
los datos y vectores en datos/ y las configuraciones de ejemplo en configuraciones/.

En Windows, usa .venv\Scripts\python.exe en lugar de .venv/bin/python.
