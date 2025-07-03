import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
# import plotly.express as px

# Configuración de la página
st.set_page_config(
    page_title="Rendimiento por Rango",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={'Get Help': 'mailto:alfredo.rubilar@gmail.com'}
)

# Título de la aplicación
st.title("_*Rendimiento* por :blue[RANGO]_")
st.subheader("Creado por :red[Alfredo Rubilar]", divider=True)
st.info(
    """
    Funcionamiento:
    1. Cargar el archivo :blue["Control Tag"] que define los rangos.
    2. Cargar el archivo :blue["INV"] con los datos generales.
    3. Procesar ambos archivos y los resultados se mostrarán automáticamente.
    """
)
st.divider()

# Inicializar session_state
if "control_tag_df" not in st.session_state:
    st.session_state.control_tag_df = None

if "inv_data" not in st.session_state:
    st.session_state.inv_data = None

# Subir archivos
uploaded_control_tag = st.file_uploader(
    "*Cargar archivo Control Tag (TXT):*", type=["txt"])
uploaded_inv = st.file_uploader("*Cargar archivo INV (TXT):*", type=["txt"])

# Procesar archivo Control Tag
if uploaded_control_tag is not None:
    control_tag_content = uploaded_control_tag.read().decode("utf-8").splitlines()
    control_tag_data = []

    for fila in control_tag_content:
        columnas = fila.split(",")
        try:
            tag_inicio = int(columnas[0])
            tag_fin = int(columnas[1])
            area = str(columnas[2]) if len(columnas) > 2 else "Sin área"
            control_tag_data.append([tag_inicio, tag_fin, area])
        except (IndexError, ValueError):
            continue  # Ignorar filas mal formateadas

    control_tag_df = pd.DataFrame(control_tag_data, columns=[
                                  "TAG Inicio", "TAG Fin", "Área"])
    st.session_state.control_tag_df = control_tag_df
    st.success("**:green[✅ Archivo Control Tag cargado correctamente.]**")

# Procesar archivo INV
if uploaded_inv is not None:
    inv_content = uploaded_inv.read().decode("utf-8").splitlines()
    inv_data = []

    for fila in inv_content:
        columnas = fila.split(",")
        try:
            # Limpia signos y ceros iniciales
            unidades = int(columnas[5].lstrip("+-0") or 0)
            timestamp = pd.to_datetime(columnas[6], format="%m/%d/%Y %H:%M:%S")
            operador = columnas[2]
            tag = int(columnas[3])
            inv_data.append([operador, tag, unidades, timestamp])
        except (IndexError, ValueError):
            continue  # Ignorar filas mal formateadas

    inv_df = pd.DataFrame(
        inv_data, columns=["Operador", "TAG", "Unidades", "Timestamp"])
    st.session_state.inv_data = inv_df
    st.success("**:green[✅ Archivo INV cargado correctamente.]**")

    # Validar existencia de datos para análisis
    if st.session_state.control_tag_df is not None and st.session_state.inv_data is not None:
        # Filtrar por rango de fechas y horas
        st.header("Filtrar por Rango de Fechas y Horas")
        min_fecha = st.session_state.inv_data["Timestamp"].min(
        ).to_pydatetime()
        max_fecha = st.session_state.inv_data["Timestamp"].max(
        ).to_pydatetime()

        rango_fecha = st.slider(
            "Seleccionar rango de fechas y horas:",
            min_value=min_fecha,
            max_value=max_fecha,
            value=(min_fecha, max_fecha),
            format="YYYY-MM-DD HH:mm"
        )

        fecha_inicio, fecha_fin = rango_fecha
        rango_filtrado_df = st.session_state.inv_data[
            (st.session_state.inv_data["Timestamp"] >= fecha_inicio) &
            (st.session_state.inv_data["Timestamp"] <= fecha_fin)
        ]

        if rango_filtrado_df.empty:
            st.warning(
                "No hay datos dentro del rango de fechas y horas seleccionado.")
        else:
            st.success(
                "Datos filtrados correctamente por rango de fechas y horas.")
            st.session_state.inv_data = rango_filtrado_df

            # Procesar y analizar datos filtrados
            if st.button("Procesar y Analizar", type="primary"):
                st.header("Resultados del Análisis")
                # Aquí iría el análisis detallado como en el código original
                tab1, tab2, tab3 = st.tabs(
                    ["Análisis por Rango", "Unidades - Contadores", "Evol. PH"])

                with tab1:

                    resultados = []
                    for _, rango in st.session_state.control_tag_df.iterrows():
                        tag_inicio = rango["TAG Inicio"]
                        tag_fin = rango["TAG Fin"]
                        area = rango["Área"]

                        # Filtrar datos en el rango
                        rango_df = st.session_state.inv_data[
                            (st.session_state.inv_data["TAG"] >= tag_inicio) &
                            (st.session_state.inv_data["TAG"] <= tag_fin)
                        ]

                        if rango_df.empty:
                            continue

                        # Calcular métricas para el rango
                        operadores_unicos = rango_df["Operador"].nunique()
                        tiempo_inicial = rango_df["Timestamp"].min()
                        tiempo_final = rango_df["Timestamp"].max()
                        horas = (tiempo_final -
                                 tiempo_inicial).total_seconds() / 3600
                        total_unidades = rango_df["Unidades"].sum()
                        ph = total_unidades / \
                            (horas * operadores_unicos) if horas > 0 and operadores_unicos > 0 else 0

                        # Agregar resultados
                        resultados.append({
                            "Área": area,
                            "TAG Inicio": tag_inicio,
                            "TAG Fin": tag_fin,
                            "Tiempo Inicial": tiempo_inicial,
                            "Tiempo Final": tiempo_final,
                            "Duración (Horas)": horas,
                            "Total Unidades": total_unidades,
                            "Operadores Únicos": operadores_unicos,
                            "PH (Producción/Hora)": ph
                        })

                    # Mostrar resultados
                    if resultados:
                        resultados_df = pd.DataFrame(resultados)
                        resultados_df["Duración (Horas)"] = resultados_df["Duración (Horas)"].round(
                            2)
                        resultados_df["PH (Producción/Hora)"] = resultados_df["PH (Producción/Hora)"].round(
                            2)

                        st.write("**Resultados del análisis por rango:**")
                        st.dataframe(resultados_df)

                        # Mostrar métricas globales
                        st.header("Análisis General")
                        tiempo_inicial_global = resultados_df["Tiempo Inicial"].min(
                        )
                        tiempo_final_global = resultados_df["Tiempo Final"].max(
                        )
                        horas = (tiempo_final_global -
                                 tiempo_inicial_global).total_seconds() / 3600
                        total_unidades = resultados_df["Total Unidades"].sum()
                        operadores_unicos_t = rango_filtrado_df["Operador"].nunique(
                        )
                        ph_global = total_unidades / \
                            (horas * operadores_unicos_t) if horas > 0 else 0

                        st.write(f"Duración Total: {horas:.2f} horas")
                        st.write(f"Total Unidades: {total_unidades}")
                        st.write(f"Operadores: {operadores_unicos_t}")
                        st.write(f"PH Global: {ph_global:.2f}")

                    else:
                        st.warning(
                            "No se encontraron datos válidos para los rangos especificados.")

                    # Asegurarnos de que el DataFrame global no esté vacío

                        # Crear gráfico de barras acumulativas para las unidades

                with tab2:
                    if not rango_filtrado_df.empty:
                        # Crear una nueva columna con intervalos de 30 minutos
                        rango_filtrado_df["Intervalo"] = rango_filtrado_df["Timestamp"].dt.floor(
                            "30T")

                        # Unidades contadas cada 30 minutos
                        unidades_acumuladas = rango_filtrado_df.groupby(
                            "Intervalo")["Unidades"].sum().cumsum()

                        # Operadores únicos cada 30 minutos
                        operadores_unicos_t = rango_filtrado_df.groupby("Intervalo")[
                            "Operador"].nunique()
                        operadores_unicos_t = operadores_unicos_t.astype(int)

                        fig1, ax1 = plt.subplots(figsize=(10, 5))
                        unidades_acumuladas.plot(
                            kind="bar", ax=ax1, color="skyblue", label="Unidades acumuladas")
                        ax1.set_title(
                            "Unidades contadas acumuladas cada 30 minutos")
                        ax1.set_xlabel("Intervalo de tiempo")
                        ax1.set_ylabel("Unidades acumuladas")
                        ax1.legend()
                        fig2, ax2 = plt.subplots(figsize=(10, 5))
                        operadores_unicos_t.plot(
                            ax=ax2, color="orange", label="Operadores activos")
                        ax2.set_title(
                            "Tendencia de operadores únicos activos cada 30 minutos")
                        ax2.set_xlabel("Intervalo de tiempo")
                        ax2.set_ylabel("Operadores únicos")
                        ax2.legend()
                        st.pyplot(fig1)
                        st.pyplot(fig2)

                with tab3:
                    # Crear una nueva columna con el rango de hora
                    rango_filtrado_df["Hora"] = rango_filtrado_df["Timestamp"].dt.floor(
                        "H")

                    # Agrupar por hora
                    ph_por_hora = rango_filtrado_df.groupby("Hora").agg(
                        Unidades_totales=("Unidades", "sum"),
                        Operadores_unicos=("Operador", "nunique"),
                        Tiempo_inicial=("Timestamp", "min"),
                        Tiempo_final=("Timestamp", "max")
                    ).reset_index()
                    # Calcular la duración en horas para cada rango de tiempo
                    ph_por_hora["Duracion_horas"] = (
                        (ph_por_hora["Tiempo_final"] -
                         ph_por_hora["Tiempo_inicial"]).dt.total_seconds() / 3600
                    )

                    # Calcular el PH para cada rango de hora
                    ph_por_hora["PH"] = ph_por_hora.apply(
                        lambda row: row["Unidades_totales"] /
                        (row["Duracion_horas"] * row["Operadores_unicos"])
                        if row["Duracion_horas"] > 0 and row["Operadores_unicos"] > 0
                        else 0,
                        axis=1
                    )

                    # Seleccionar columnas relevantes para el resultado final
                    resultado_ph = ph_por_hora[[
                        "Hora", "Unidades_totales", "Operadores_unicos", "Duracion_horas", "PH"]]
                    resultado_ph["PH"] = resultado_ph["PH"].astype(int)
                    st.header("_*Evolución PH por :red[hora].*_")

                    # Mostrar el DataFrame resultante en Streamlit
                    st.write("Evolución del PH por rango de hora:")
                    st.dataframe(resultado_ph)

                    # Verificar que el DataFrame no esté vacío
                    if not resultado_ph.empty:
                        # Crear figura y eje
                        fig, ax = plt.subplots(figsize=(10, 6))

                        # Plotear el gráfico de tendencia
                        ax.plot(
                            resultado_ph["Hora"],
                            resultado_ph["PH"],
                            marker="o",
                            linestyle="-",
                            color="blue",
                            label="PH (Producción por hora)"
                        )

                        # Configurar etiquetas y título
                        ax.set_xlabel("Hora")
                        ax.set_ylabel("PH (Producción por Hora)")
                        ax.set_title("Tendencia del PH por Hora")
                        ax.grid(True)
                        ax.legend()

                        # Rotar etiquetas del eje X para mejor visibilidad
                        plt.xticks(rotation=45)

                        # Mostrar gráfico en Streamlit
                        st.pyplot(fig)
