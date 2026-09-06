import streamlit as st
from PIL import Image
import pandas as pd
import os
from datetime import datetime

st.set_page_config(
    page_title="Third Molar Measurement",
    page_icon="🦷",
    layout="wide"
)

st.title("🦷 Third Molar Measurement")
st.caption("Manual third molar measurement and automatic I3M calculation")

MASTER_FILE = "Third_Molar_MASTER.xlsx"

TEETH = ["18", "28", "38", "48"]

# ---------------------------------------------------------
# SUBJECT
# ---------------------------------------------------------
st.subheader("Subject")

c1, c2, c3 = st.columns(3)

with c1:
    subject_id = st.text_input("Subject ID")

with c2:
    age = st.number_input(
        "Age (years)",
        min_value=0.0,
        max_value=100.0,
        step=0.01,
        format="%.2f"
    )

with c3:
    sex = st.selectbox("Sex", ["", "Female", "Male"])

st.divider()

# ---------------------------------------------------------
# RADIOGRAPH
# ---------------------------------------------------------
st.subheader("Panoramic radiograph")

uploaded_file = st.file_uploader(
    "Upload OPT",
    type=["jpg", "jpeg", "png", "tif", "tiff"]
)

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, use_container_width=True)

st.divider()

# ---------------------------------------------------------
# TOOTH
# ---------------------------------------------------------
st.subheader("Third molar")

tooth = st.radio(
    "Select tooth",
    TEETH,
    horizontal=True
)

root_number = st.radio(
    "Number of apical openings",
    [1, 2],
    horizontal=True,
    key=f"roots_{tooth}"
)

st.markdown(
    "🔴 **RED = apical opening(s)**  \n"
    "🔵 **BLUE = tooth height**"
)

# ---------------------------------------------------------
# MEASUREMENTS
# ---------------------------------------------------------
if root_number == 1:

    c1, c2 = st.columns(2)

    with c1:
        a1 = st.number_input(
            f"🔴 {tooth} — Apical opening A1",
            min_value=0.0,
            step=0.01,
            format="%.3f",
            key=f"a1_{tooth}"
        )

    a2 = 0.0

    with c2:
        height = st.number_input(
            f"🔵 {tooth} — Tooth height L",
            min_value=0.0,
            step=0.01,
            format="%.3f",
            key=f"height_{tooth}"
        )

else:

    c1, c2, c3 = st.columns(3)

    with c1:
        a1 = st.number_input(
            f"🔴 {tooth} — Apical opening A1",
            min_value=0.0,
            step=0.01,
            format="%.3f",
            key=f"a1_{tooth}"
        )

    with c2:
        a2 = st.number_input(
            f"🔴 {tooth} — Apical opening A2",
            min_value=0.0,
            step=0.01,
            format="%.3f",
            key=f"a2_{tooth}"
        )

    with c3:
        height = st.number_input(
            f"🔵 {tooth} — Tooth height L",
            min_value=0.0,
            step=0.01,
            format="%.3f",
            key=f"height_{tooth}"
        )

# ---------------------------------------------------------
# I3M
# ---------------------------------------------------------
if height > 0:
    ratio = (a1 + a2) / height

    st.metric(
        f"I3M — Tooth {tooth}",
        f"{ratio:.4f}"
    )

    if root_number == 1:
        st.caption("I3M = A1 / L")
    else:
        st.caption("I3M = (A1 + A2) / L")
else:
    ratio = None

# ---------------------------------------------------------
# SESSION STORAGE
# ---------------------------------------------------------
if "measurements" not in st.session_state:
    st.session_state.measurements = {}

if st.button(f"Save measurement for tooth {tooth}"):

    if height <= 0:
        st.error("Tooth height must be greater than zero.")

    else:
        st.session_state.measurements[tooth] = {
            "Openings": root_number,
            "A1": a1,
            "A2": a2 if root_number == 2 else None,
            "Height": height,
            "I3M": ratio
        }

        st.success(f"Tooth {tooth} saved.")

# ---------------------------------------------------------
# CURRENT MEASUREMENTS
# ---------------------------------------------------------
if st.session_state.measurements:

    st.subheader("Current measurements")

    table = []

    for t in TEETH:
        if t in st.session_state.measurements:

            m = st.session_state.measurements[t]

            table.append({
                "Tooth": t,
                "Openings": m["Openings"],
                "A1": round(m["A1"], 3),
                "A2": (
                    round(m["A2"], 3)
                    if m["A2"] is not None
                    else ""
                ),
                "Height": round(m["Height"], 3),
                "I3M": round(m["I3M"], 4)
            })

    st.dataframe(
        pd.DataFrame(table),
        use_container_width=True
    )

st.divider()

# ---------------------------------------------------------
# SAVE SUBJECT
# ---------------------------------------------------------
st.subheader("Save subject")

if st.button(
    "💾 SAVE SUBJECT TO MASTER FILE",
    type="primary"
):

    if subject_id.strip() == "":
        st.error("Enter Subject ID.")

    elif not st.session_state.measurements:
        st.error("No tooth measurements have been saved.")

    else:

        row = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "ID": subject_id,
            "Age": age,
            "Sex": sex
        }

        for t in TEETH:

            if t in st.session_state.measurements:

                m = st.session_state.measurements[t]

                row[f"{t}_Openings"] = m["Openings"]
                row[f"{t}_A1"] = m["A1"]
                row[f"{t}_A2"] = (
                    m["A2"]
                    if m["A2"] is not None
                    else ""
                )
                row[f"{t}_Height"] = m["Height"]
                row[f"{t}_I3M"] = m["I3M"]

            else:

                row[f"{t}_Openings"] = ""
                row[f"{t}_A1"] = ""
                row[f"{t}_A2"] = ""
                row[f"{t}_Height"] = ""
                row[f"{t}_I3M"] = ""

        new_row = pd.DataFrame([row])

        if os.path.exists(MASTER_FILE):
            old = pd.read_excel(MASTER_FILE)
            df = pd.concat(
                [old, new_row],
                ignore_index=True
            )
        else:
            df = new_row

        df.to_excel(
            MASTER_FILE,
            index=False
        )

        st.success(
            f"Subject {subject_id} saved successfully."
        )

        st.session_state.measurements = {}
