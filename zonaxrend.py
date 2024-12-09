import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(
    page_title="Rendimiento por Rango",
    #page_icon="\ud83d\udcca",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:alfredo.rubilar@gmail.com',
    }
)

# Configurar título de la aplicación
st.title("_*Rendimiento* por :blue[RANGO]_")
st.subheader("Creado por :red[Alfredo Rubilar]", divider=True)
st.info(
    """
    Funcionamiento:\n
    1.- Cargar el archivo :blue["Control Tag"] que define los rangos.\n
    2.- Cargar el archivo :blue["INV"] con los datos generales.\n
    3.- Procesar ambos archivos y los resultados se mostrarán automáticamente.
    """
)
st.divider()

# Subir archivos
uploaded_control_tag = st.file_uploader("*Cargar archivo Control Tag (TXT):*", type=["txt"])
uploaded_inv = st.file_uploader("*Cargar archivo INV (TXT):*", type=["txt"])

if uploaded_control_tag is not None and uploaded_inv is not None:
    # Leer y procesar el archivo Control Tag
    if "control_tag" not in st.session_state:
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

        control_tag_df = pd.DataFrame(control_tag_data, columns=["TAG Inicio", "TAG Fin", "Área"])
        st.session_state.control_tag = control_tag_df

    st.success("**:green[✅ Archivo Control Tag cargado correctamente.]**")

    # Leer y procesar el archivo INV
    if "inv_data" not in st.session_state:
        inv_content = uploaded_inv.read().decode("utf-8").splitlines()
        inv_data = []

        for fila in inv_content:
            columnas = fila.split(",")
            try:
                unidades = int(columnas[5].lstrip("+-0") or 0)  # Limpia signos y ceros iniciales
                timestamp = pd.to_datetime(columnas[6], format="%m/%d/%Y %H:%M:%S")
                operador = columnas[2]
                tag = int(columnas[3])
                inv_data.append([operador, tag, unidades, timestamp])
            except (IndexError, ValueError):
                continue  # Ignorar filas mal formateadas

        inv_df = pd.DataFrame(inv_data, columns=["Operador", "TAG", "Unidades", "Timestamp"])
        st.session_state.inv_data = inv_df

    st.success("**:green[✅ Archivo INV cargado correctamente.]**")

    # Seleccionar rango de fechas y horas
    st.header("Filtrar por Rango de Fechas y Horas")
    min_fecha = st.session_state.inv_data["Timestamp"].min().to_pydatetime()
    max_fecha = st.session_state.inv_data["Timestamp"].max().to_pydatetime()

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
        st.warning("No hay datos dentro del rango de fechas y horas seleccionado.")
    else:
        st.success("Datos filtrados correctamente por rango de fechas y horas.")
        st.session_state.inv_data = rango_filtrado_df

    # Procesar y analizar datos filtrados
    if st.button("Procesar y Analizar", type="primary"):
        st.header("Resultados del Análisis")

        resultados = []
        for _, rango in st.session_state.control_tag.iterrows():
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
            horas = (tiempo_final - tiempo_inicial).total_seconds() / 3600
            total_unidades = rango_df["Unidades"].sum()
            ph = total_unidades / (horas * operadores_unicos) if horas > 0 and operadores_unicos > 0 else 0

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
            resultados_df["Duración (Horas)"] = resultados_df["Duración (Horas)"].round(2)
            resultados_df["PH (Producción/Hora)"] = resultados_df["PH (Producción/Hora)"].round(2)

            st.write("**Resultados del análisis por rango:**")
            st.dataframe(resultados_df)

            # Mostrar métricas globales
            st.header("Análisis General")
            tiempo_inicial_global = resultados_df["Tiempo Inicial"].min()
            tiempo_final_global = resultados_df["Tiempo Final"].max()
            horas = (tiempo_final_global - tiempo_inicial_global).total_seconds() / 3600
            total_unidades = resultados_df["Total Unidades"].sum()
            operadores_unicos_t = rango_filtrado_df["Operador"].nunique()
            ph_global = total_unidades / (horas * operadores_unicos_t) if horas > 0 else 0

            st.write(f"Duración Total: {horas:.2f} horas")
            st.write(f"Total Unidades: {total_unidades}")
            st.write(f"Operadores: {operadores_unicos_t}")
            st.write(f"PH Global: {ph_global:.2f}")

        else:
            st.warning("No se encontraron datos válidos para los rangos especificados.")
