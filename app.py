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
st.caption("Manual I3M measurement and automatic data recording")

# ---------------------------------------------------------
# MASTER FILE
# ---------------------------------------------------------
MASTER_FILE = "Third_Molar_MASTER.xlsx"

columns = [
    "Date", "ID", "Age", "Sex",
    "18_Apex", "18_Height", "18_I3M",
    "28_Apex", "28_Height", "28_I3M",
    "38_Apex", "38_Height", "38_I3M",
    "48_Apex", "48_Height", "48_I3M"
]

# ---------------------------------------------------------
# SUBJECT DATA
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
# IMAGE
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
# TOOTH SELECTION
# ---------------------------------------------------------
st.subheader("Third molar")

tooth = st.radio(
    "Select tooth",
    ["18", "28", "38", "48"],
    horizontal=True
)

st.info(
    "🔴 APEX = measure the apical opening\n\n"
    "🔵 HEIGHT = measure tooth height"
)

# ---------------------------------------------------------
# MANUAL MEASUREMENTS
# ---------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    apex = st.number_input(
        f"🔴 {tooth} — Apical opening",
        min_value=0.0,
        step=0.01,
        format="%.3f",
        key=f"apex_{tooth}"
    )

with c2:
    height = st.number_input(
        f"🔵 {tooth} — Tooth height",
        min_value=0.0,
        step=0.01,
        format="%.3f",
        key=f"height_{tooth}"
    )

if height > 0:
    ratio = apex / height
    st.metric(f"I3M — Tooth {tooth}", f"{ratio:.4f}")
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
            "Apex": apex,
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

    for t in ["18", "28", "38", "48"]:
        if t in st.session_state.measurements:
            m = st.session_state.measurements[t]
            table.append({
                "Tooth": t,
                "Apex": round(m["Apex"], 3),
                "Height": round(m["Height"], 3),
                "I3M": round(m["I3M"], 4)
            })

    st.dataframe(pd.DataFrame(table), use_container_width=True)

st.divider()

# ---------------------------------------------------------
# SAVE SUBJECT TO MASTER
# ---------------------------------------------------------
st.subheader("Save subject")

if st.button("💾 SAVE SUBJECT TO MASTER FILE", type="primary"):

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

        for t in ["18", "28", "38", "48"]:
            if t in st.session_state.measurements:
                m = st.session_state.measurements[t]
                row[f"{t}_Apex"] = m["Apex"]
                row[f"{t}_Height"] = m["Height"]
                row[f"{t}_I3M"] = m["I3M"]
            else:
                row[f"{t}_Apex"] = ""
                row[f"{t}_Height"] = ""
                row[f"{t}_I3M"] = ""

        new_row = pd.DataFrame([row], columns=columns)

        if os.path.exists(MASTER_FILE):
            old = pd.read_excel(MASTER_FILE)
            df = pd.concat([old, new_row], ignore_index=True)
        else:
            df = new_row

        df.to_excel(MASTER_FILE, index=False)

        st.success(
            f"Subject {subject_id} saved successfully in {MASTER_FILE}"
        )

        st.session_state.measurements = {}
