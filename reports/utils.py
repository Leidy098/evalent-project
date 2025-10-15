# reports/utils.py
from io import BytesIO
import matplotlib
matplotlib.use("Agg")  # backend sin GUI
import matplotlib.pyplot as plt

def compute_scores(interview):
    scores = [getattr(m, "score", None) for m in interview.messages.all()]
    scores = [s for s in scores if s is not None]
    if scores:
        promedio = {
            "claridad": sum(s.claridad for s in scores) / len(scores),
            "confianza": sum(s.confianza for s in scores) / len(scores),
            "contenido": sum(s.contenido for s in scores) / len(scores),
            "creatividad": sum(s.creatividad for s in scores) / len(scores),
            "lenguaje": sum(s.lenguaje for s in scores) / len(scores),
        }
    else:
        promedio = {"claridad": 0, "confianza": 0, "contenido": 0, "creatividad": 0, "lenguaje": 0}
    puntaje = int(sum(promedio.values()) / 5)
    comparativa = [60, 75, puntaje]  # como en tu results
    return promedio, puntaje, comparativa

def matplotlib_to_png_bytes(plt_figure):
    buf = BytesIO()
    plt_figure.savefig(buf, format="png", bbox_inches="tight")
    plt.close(plt_figure)
    buf.seek(0)
    return buf

def plot_promedios(promedio_dict):
    labels = list(promedio_dict.keys())
    values = [promedio_dict[k] for k in labels]
    fig = plt.figure()
    plt.title("Promedio por criterio")
    plt.bar(labels, values)
    plt.ylim(0, 100)
    plt.xlabel("Criterios")
    plt.ylabel("Puntaje")
    return matplotlib_to_png_bytes(fig)

def plot_comparativa(comparativa):
    labels = ["Cohorte", "Top 25%", "Tú"]
    fig = plt.figure()
    plt.title("Comparativa")
    plt.bar(labels, comparativa)
    plt.ylim(0, 100)
    plt.ylabel("Puntaje")
    return matplotlib_to_png_bytes(fig)

def plot_radar(promedio_dict):
    import matplotlib.pyplot as plt
    import numpy as np
    from io import BytesIO

    labels = np.array(list(promedio_dict.keys()))
    values = np.array([promedio_dict[k] for k in labels])
    num_vars = len(labels)

    # Cerrar el gráfico anterior
    plt.close()

    # Crear radar chart
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    values = np.concatenate((values, [values[0]]))
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.fill(angles, values, color="#0d6efd", alpha=0.25)
    ax.plot(angles, values, color="#0d6efd", linewidth=2)
    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    plt.title("Radar de Desempeño", size=14, color="#0d6efd", pad=20)

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close()
    return buf


def plot_pie_strengths(promedio_dict):
    import matplotlib.pyplot as plt
    from io import BytesIO

    labels = ["Fortalezas", "Debilidades"]
    strengths = sum(1 for v in promedio_dict.values() if v >= 60)
    weaknesses = sum(1 for v in promedio_dict.values() if v < 60)
    data = [strengths, weaknesses]

    fig, ax = plt.subplots()
    ax.pie(
        data,
        labels=labels,
        autopct="%1.0f%%",
        startangle=90,
        colors=["#198754", "#dc3545"],
        textprops={"color": "black"},
    )
    ax.set_title("Distribución de Fortalezas vs Debilidades")

    buf = BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    plt.close()
    return buf
