"""Comparación pareada por bloques de objetivos."""
import numpy as np
import pandas as pd
from scipy.stats import binomtest


# Compara dos modelos sobre las mismas consultas y estima incertidumbre agrupando por objetivo.
def comparar_pareado(detalle, modelo_a, modelo_b, metrica='hit@5', repeticiones=2000, semilla=1950):
    """Bootstrap por objetivo: todas sus glosas permanecen en el mismo bloque.

    McNemar exacto es exploratorio por consulta; no corrige dependencia ni
    comparaciones múltiples. El IC por bloques es la referencia principal.
    """
    if repeticiones < 1:
        raise ValueError('Se necesita al menos una repetición.')
    if metrica not in ('hit@1', 'hit@3', 'hit@5', 'hit@1_alias', 'hit@3_alias', 'hit@5_alias'):
        raise ValueError('Esta comparación requiere una métrica binaria Hit@k.')
    partes = []
    for nombre in (modelo_a, modelo_b):
        parte = detalle.loc[detalle.modelo.eq(nombre), ['id', 'objetivo', metrica]].copy()
        if parte.id.duplicated().any():
            raise ValueError('Mezcla de experimentos o ids repetidos.')
        partes.append(parte.set_index('id'))
    a, b = partes
    if a.empty or set(a.index) != set(b.index):
        raise ValueError('La comparación pareada necesita exactamente las mismas consultas.')
    b = b.loc[a.index]
    if not a.objetivo.equals(b.objetivo):
        raise ValueError('Un id tiene objetivos diferentes entre modelos.')
    diferencia = a[metrica] - b[metrica]
    grupos = diferencia.groupby(a.objetivo).agg(['sum', 'count']).to_numpy()
    rng = np.random.default_rng(semilla)
    muestras = np.empty(repeticiones)
    for i in range(repeticiones):
        seleccion = grupos[rng.integers(0, len(grupos), size=len(grupos))]
        muestras[i] = seleccion[:, 0].sum() / seleccion[:, 1].sum()
    gana_a = int(((a[metrica] == 1) & (b[metrica] == 0)).sum())
    gana_b = int(((a[metrica] == 0) & (b[metrica] == 1)).sum())
    return pd.DataFrame([dict(modelo_a=modelo_a, modelo_b=modelo_b, metrica=metrica, n=len(a),
                              conceptos=len(grupos), diferencia=diferencia.mean(),
                              ic_inferior=np.quantile(muestras, .025), ic_superior=np.quantile(muestras, .975),
                              gana_a=gana_a, gana_b=gana_b,
                              p_mcnemar=binomtest(gana_a, gana_a+gana_b).pvalue if gana_a+gana_b else 1.,
                              repeticiones=repeticiones, semilla=semilla)])

