import streamlit as st
from PIL import Image, ImageDraw
import pandas as pd
import math
from datetime import datetime
from io import BytesIO
from streamlit_image_coordinates import streamlit_image_coordinates
from supabase import create_client
# Supabase connection
@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = get_supabase()

st.set_page_config(
    page_title="Third Molar Measurement",
    page_icon="🦷",
    layout="wide"
)

st.title("🦷 Third Molar Measurement")
st.caption("Direct measurement on panoramic radiograph")

TEETH = ["18", "28", "38", "48"]

# =========================================================
# SESSION STATE
# =========================================================
if "points" not in st.session_state:
    st.session_state.points = {}

if "measurements" not in st.session_state:
    st.session_state.measurements = {}

if "master_data" not in st.session_state:
    st.session_state.master_data = []

if "selected_tooth" not in st.session_state:
    st.session_state.selected_tooth = "18"

if "last_click" not in st.session_state:
    st.session_state.last_click = None

if "subject_id" not in st.session_state:
    st.session_state.subject_id = ""

if "age" not in st.session_state:
    st.session_state.age = 0.0

if "sex" not in st.session_state:
    st.session_state.sex = ""

# =========================================================
# SUBJECT
# =========================================================
st.subheader("Subject")

c1, c2, c3 = st.columns(3)

with c1:
    subject_id = st.text_input(
        "Subject ID",
        key="subject_id"
    )

with c2:
    age = st.number_input(
        "Age (years)",
        min_value=0.0,
        max_value=100.0,
        step=0.01,
        format="%.2f",
        key="age"
    )

with c3:
    sex = st.selectbox(
        "Sex",
        ["", "Female", "Male"],
        key="sex"
    )

# =========================================================
# IMAGE
# =========================================================
st.subheader("Panoramic radiograph")

uploaded_file = st.file_uploader(
    "Upload OPT",
    type=["jpg", "jpeg", "png"],
    key="uploaded_opt"
)

if uploaded_file is not None:

    image = Image.open(uploaded_file).convert("RGB")

    # =====================================================
    # TOOTH SELECTION
    # =====================================================
    st.subheader("Measurement")

    tooth = st.radio(
        "Select tooth",
        TEETH,
        horizontal=True,
        key="selected_tooth"
    )

    openings = st.radio(
        "Number of apical openings",
        [1, 2],
        horizontal=True,
        key=f"openings_{tooth}"
    )

    measurement_key = f"{tooth}_{openings}"

    if measurement_key not in st.session_state.points:
        st.session_state.points[measurement_key] = []

    points = st.session_state.points[measurement_key]

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

    # =====================================================
    # DRAW IMAGE
    # =====================================================
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

    # A1
    if len(points) >= 2:
        draw.line(
            [points[0], points[1]],
            fill="red",
            width=4
        )

    # A2
    if openings == 2 and len(points) >= 4:
        draw.line(
            [points[2], points[3]],
            fill="red",
            width=4
        )

    # L
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

    # =====================================================
    # CLICKABLE IMAGE
    # =====================================================
    value = streamlit_image_coordinates(
        display_image,
        key=f"image_{tooth}_{openings}_{len(points)}"
    )

    if value is not None and len(points) < required_points:

        click = (
            int(value["x"]),
            int(value["y"])
        )

        if click != st.session_state.last_click:

            st.session_state.points[measurement_key].append(click)
            st.session_state.last_click = click

            st.rerun()

    # =====================================================
    # CONTROLS
    # =====================================================
    c1, c2 = st.columns(2)

    with c1:
        if st.button(
            "↩️ Undo last point",
            key=f"undo_{tooth}_{openings}"
        ):
            if st.session_state.points[measurement_key]:
                st.session_state.points[measurement_key].pop()
                st.session_state.last_click = None
                st.rerun()

    with c2:
        if st.button(
            "🗑️ Reset measurement",
            key=f"reset_{tooth}_{openings}"
        ):
            st.session_state.points[measurement_key] = []
            st.session_state.last_click = None
            st.rerun()

    st.write(
        f"Points selected: **{len(points)} / {required_points}**"
    )

    # =====================================================
    # DISTANCE
    # =====================================================
    def distance(p1, p2):
        return math.sqrt(
            (p2[0] - p1[0]) ** 2 +
            (p2[1] - p1[1]) ** 2
        )

    # =====================================================
    # CALCULATION
    # =====================================================
    if len(points) == required_points:

        if openings == 1:

            A1 = distance(
                points[0],
                points[1]
            )

            A2 = None

            L = distance(
                points[2],
                points[3]
            )

            I3M = A1 / L if L > 0 else None

        else:

            A1 = distance(
                points[0],
                points[1]
            )

            A2 = distance(
                points[2],
                points[3]
            )

            L = distance(
                points[4],
                points[5]
            )

            I3M = (
                (A1 + A2) / L
                if L > 0
                else None
            )

        st.success("Measurement complete")

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "A1",
            f"{A1:.2f} px"
        )

        if A2 is not None:
            c2.metric(
                "A2",
                f"{A2:.2f} px"
            )
        else:
            c2.metric(
                "A2",
                "—"
            )

        c3.metric(
            "L",
            f"{L:.2f} px"
        )

        c4.metric(
            "I3M",
            f"{I3M:.4f}"
        )

        if openings == 1:
            st.caption("I3M = A1 / L")
        else:
            st.caption("I3M = (A1 + A2) / L")

        if st.button(
            f"✅ Save tooth {tooth}",
            key=f"save_{tooth}_{openings}"
        ):

            st.session_state.measurements[tooth] = {
                "Openings": openings,
                "A1": A1,
                "A2": A2,
                "Height": L,
                "I3M": I3M
            }

            st.success(
                f"Tooth {tooth} saved."
            )

else:
    st.info(
        "Upload a panoramic radiograph to start measuring."
    )

# =========================================================
# CURRENT SUBJECT
# =========================================================
if st.session_state.measurements:

    st.divider()
    st.subheader("Current subject measurements")

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
                "Height": round(
                    m["Height"],
                    2
                ),
                "I3M": round(
                    m["I3M"],
                    4
                )
            })

    st.dataframe(
        pd.DataFrame(rows),
        use_container_width=True
    )

# =========================================================
# SAVE SUBJECT TO MASTER
# =========================================================
st.divider()
st.subheader("Master dataset")

if st.button("💾 ADD SUBJECT TO MASTER", type="primary"):

    if not st.session_state.subject_id.strip():
        st.error("Enter Subject ID.")

    elif not st.session_state.measurements:
        st.error("No tooth measurements saved.")

    else:
        db_row = {
            "subject_id": st.session_state.subject_id,
            "age": st.session_state.age,
            "sex": st.session_state.sex
        }

        for t in TEETH:
            m = st.session_state.measurements.get(t)

            db_row[f"{t}_openings"] = m["Openings"] if m else None
            db_row[f"{t}_a1_px"] = m["A1"] if m else None
            db_row[f"{t}_a2_px"] = m["A2"] if m else None
            db_row[f"{t}_height_px"] = m["Height"] if m else None
            db_row[f"{t}_i3m"] = m["I3M"] if m else None

        try:
            supabase.table("third_molar_data").insert(db_row).execute()
            st.success(
                f"Subject {st.session_state.subject_id} added to shared master."
            )
        except Exception as e:
            st.error(f"Unable to save subject: {e}")
# =========================================================
# MASTER TABLE + EXCEL
# =========================================================
if st.button("🔄 REFRESH SHARED MASTER"):
    try:
        response = (
            supabase
            .table("third_molar_data")
            .select("*")
            .order("id")
            .execute()
        )

        master_df = pd.DataFrame(response.data)

        if not master_df.empty:
            st.write(
                f"Subjects in shared master: **{len(master_df)}**"
            )

            st.dataframe(
                master_df,
                use_container_width=True
            )

            excel_buffer = BytesIO()

            with pd.ExcelWriter(
                excel_buffer,
                engine="openpyxl"
            ) as writer:
                master_df.to_excel(
                    writer,
                    index=False,
                    sheet_name="Third Molars"
                )

            excel_buffer.seek(0)

            st.download_button(
                label="⬇️ DOWNLOAD SHARED MASTER EXCEL",
                data=excel_buffer,
                file_name="Third_Molar_SHARED_MASTER.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.info("The shared master is currently empty.")

    except Exception as e:
        st.error(f"Unable to read shared master: {e}")
# =========================================================
## =========================================================
# NEW SUBJECT
# =========================================================
st.divider()

def new_subject():
    st.session_state.measurements = {}
    st.session_state.points = {}
    st.session_state.last_click = None

    st.session_state.subject_id = ""
    st.session_state.age = 0.0
    st.session_state.sex = ""
    st.session_state.selected_tooth = "18"

    if "uploaded_opt" in st.session_state:
        del st.session_state["uploaded_opt"]

    for t in TEETH:
        key = f"openings_{t}"
        if key in st.session_state:
            del st.session_state[key]

st.button(
    "➕ NEW SUBJECT",
    on_click=new_subject
)
