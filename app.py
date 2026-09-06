import streamlit as st
from PIL import Image, ImageDraw
import pandas as pd
import os
import math
from datetime import datetime
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(
    page_title="Third Molar Measurement",
    page_icon="🦷",
    layout="wide"
)

st.title("🦷 Third Molar Measurement")
st.caption("Direct measurement on panoramic radiograph")

MASTER_FILE = "Third_Molar_MASTER.xlsx"
TEETH = ["18", "28", "38", "48"]

# ---------- SESSION ----------
if "points" not in st.session_state:
    st.session_state.points = {}

if "measurements" not in st.session_state:
    st.session_state.measurements = {}

if "last_click" not in st.session_state:
    st.session_state.last_click = None

# ---------- SUBJECT ----------
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

# ---------- IMAGE ----------
st.subheader("Panoramic radiograph")

uploaded_file = st.file_uploader(
    "Upload OPT",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is None:
    st.info("Upload a panoramic radiograph to start.")
    st.stop()

image = Image.open(uploaded_file).convert("RGB")

# ---------- TOOTH ----------
st.subheader("Measurement")

tooth = st.radio(
    "Select tooth",
    TEETH,
    horizontal=True
)

openings = st.radio(
    "Number of apical openings",
    [1, 2],
    horizontal=True
)

key = f"{tooth}_{openings}"

if key not in st.session_state.points:
    st.session_state.points[key] = []

points = st.session_state.points[key]

required_points = 4 if openings == 1 else 6

if openings == 1:
    st.markdown(
        """
        **Click in this order:**  
        🔴 **1–2:** apical opening A1  
        🔵 **3–4:** tooth height L
        """
    )
else:
    st.markdown(
        """
        **Click in this order:**  
        🔴 **1–2:** apical opening A1  
        🔴 **3–4:** apical opening A2  
        🔵 **5–6:** tooth height L
        """
    )

# ---------- DRAW CURRENT POINTS ----------
display_image = image.copy()
draw = ImageDraw.Draw(display_image)

for i, (x, y) in enumerate(points):

    if openings == 1:
        is_apex = i < 2
    else:
        is_apex = i < 4

    color = "red" if is_apex else "blue"

    r = 7
    draw.ellipse(
        (x-r, y-r, x+r, y+r),
        fill=color,
        outline="white",
        width=2
    )

# Draw measurement lines
if len(points) >= 2:
    draw.line(
        [points[0], points[1]],
        fill="red",
        width=4
    )

if openings == 2 and len(points) >= 4:
    draw.line(
        [points[2], points[3]],
        fill="red",
        width=4
    )

if openings == 1 and len(points) >= 4:
    draw.line(
        [points[2], points[3]],
        fill="blue",
        width=4
    )

if openings == 2 and len(points) >= 6:
    draw.line(
        [points[4], points[5]],
        fill="blue",
        width=4
    )

# ---------- CLICKABLE IMAGE ----------
value = streamlit_image_coordinates(
    display_image,
    key=f"image_{key}_{len(points)}"
)

if value is not None and len(points) < required_points:

    click = (int(value["x"]), int(value["y"]))

    if click != st.session_state.last_click:
        st.session_state.points[key].append(click)
        st.session_state.last_click = click
        st.rerun()

# ---------- CONTROLS ----------
c1, c2 = st.columns(2)

with c1:
    if st.button("↩️ Undo last point"):
        if st.session_state.points[key]:
            st.session_state.points[key].pop()
            st.session_state.last_click = None
            st.rerun()

with c2:
    if st.button("🗑️ Reset measurement"):
        st.session_state.points[key] = []
        st.session_state.last_click = None
        st.rerun()

st.write(f"Points selected: **{len(points)} / {required_points}**")

# ---------- CALCULATE ----------
def distance(p1, p2):
    return math.sqrt(
        (p2[0] - p1[0]) ** 2 +
        (p2[1] - p1[1]) ** 2
    )

if len(points) == required_points:

    if openings == 1:

        A1 = distance(points[0], points[1])
        A2 = None
        L = distance(points[2], points[3])
        I3M = A1 / L if L > 0 else None

    else:

        A1 = distance(points[0], points[1])
        A2 = distance(points[2], points[3])
        L = distance(points[4], points[5])
        I3M = (A1 + A2) / L if L > 0 else None

    st.success("Measurement complete")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("A1", f"{A1:.2f} px")

    if A2 is not None:
        c2.metric("A2", f"{A2:.2f} px")
    else:
        c2.metric("A2", "—")

    c3.metric("L", f"{L:.2f} px")
    c4.metric("I3M", f"{I3M:.4f}")

    if st.button(f"✅ Save tooth {tooth}"):

        st.session_state.measurements[tooth] = {
            "Openings": openings,
            "A1": A1,
            "A2": A2,
            "Height": L,
            "I3M": I3M
        }

        st.success(f"Tooth {tooth} saved.")

# ---------- CURRENT TEETH ----------
if st.session_state.measurements:

    st.divider()
    st.subheader("Current subject")

    rows = []

    for t in TEETH:

        if t in st.session_state.measurements:

            m = st.session_state.measurements[t]

            rows.append({
                "Tooth": t,
                "Openings": m["Openings"],
                "A1": round(m["A1"], 2),
                "A2": (
                    round(m["A2"], 2)
                    if m["A2"] is not None
                    else ""
                ),
                "Height": round(m["Height"], 2),
                "I3M": round(m["I3M"], 4)
            })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True
    )

# ---------- MASTER ----------
st.divider()
st.subheader("Save subject")

if st.button(
    "💾 SAVE SUBJECT TO MASTER FILE",
    type="primary"
):

    if not subject_id.strip():
        st.error("Enter Subject ID.")

    elif not st.session_state.measurements:
        st.error("No measurements saved.")

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
                row[f"{t}_A1_px"] = m["A1"]
                row[f"{t}_A2_px"] = (
                    m["A2"]
                    if m["A2"] is not None
                    else ""
                )
                row[f"{t}_Height_px"] = m["Height"]
                row[f"{t}_I3M"] = m["I3M"]

            else:

                row[f"{t}_Openings"] = ""
                row[f"{t}_A1_px"] = ""
                row[f"{t}_A2_px"] = ""
                row[f"{t}_Height_px"] = ""
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
            f"Subject {subject_id} saved to master file."
        )
