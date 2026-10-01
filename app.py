from __future__ import annotations

import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from neo4j_service import (
    create_schema,
    get_dashboard_metrics,
    get_user_profile,
    get_users,
    get_locations,
    get_user_likes,
    get_user_friends,
    recommend_locations,
    graph_likes,
    graph_users,
    graph_neighborhood,
    seed_demo_data,
    ping,
)

st.set_page_config(
    page_title="Photography Location Recommender",
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
      .hero {
        padding: 1.5rem 1.7rem; border-radius: 22px;
        background: linear-gradient(120deg, #111827 0%, #1f2937 55%, #7c3aed 100%);
        color: white; margin-bottom: 1rem;
      }
      .hero h1 {margin:0; font-size:2.15rem;}
      .hero p {opacity:.88; margin:.35rem 0 0 0;}
      .recommend-card {
        padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.25);
        border-radius: 16px; margin-bottom: .75rem;
      }
      .score-pill {
        display:inline-block; padding:.2rem .55rem; border-radius:999px;
        background:#7c3aed; color:white; font-size:.8rem; font-weight:700;
      }
      .muted {opacity:.72; font-size:.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def require_connection() -> None:
    try:
        if not ping():
            raise RuntimeError("Neo4j did not return a healthy response")
    except Exception as exc:
        st.error("ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "neo4j"\npassword = "YOUR_PASSWORD"\ndatabase = "neo4j"',
            language="toml",
        )
        st.caption("ให้นำค่าไปใส่ใน Streamlit Secrets และห้าม commit password ลง GitHub")
        st.exception(exc)
        st.stop()


def user_selector(key: str = "user") -> str:
    users = get_users()
    if not users:
        st.info("ยังไม่มีข้อมูล User กรุณาไปหน้า Admin / Setup แล้วสร้างข้อมูลตัวอย่าง")
        st.stop()
    labels = {x["name"]: x["name"] for x in users}
    chosen = st.selectbox("เลือก User", list(labels), key=key)
    return labels[chosen]


require_connection()

with st.sidebar:
    st.markdown("## 📷 Photography Graph")
    st.caption("Neo4j Aura + Streamlit")
    page = st.radio(
        "เมนู",
        ["Dashboard", "Recommendations", "User & Location", "Graph Explorer", "Cypher Examples", "Admin / Setup"],
    )
    st.divider()
    st.caption("Photography Location Recommender")


st.markdown(
    """
    <div class="hero">
      <h1>📷 Photography Location Recommender</h1>
      <p>ระบบแนะนำสถานที่ถ่ายรูปด้วย Graph Database และ Neo4j</p>
    </div>
    """,
    unsafe_allow_html=True,
)


if page == "Dashboard":
    st.subheader("ภาพรวม Graph")
    m = get_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", m["users"])
    c2.metric("Locations", m["locations"])
    c3.metric("LIKES", m["likes"])
    c4.metric("FRIEND", m["friends"])

    st.divider()
    selected = user_selector("dash_user")
    profile = get_user_profile(selected)

    if profile:
        left, right = st.columns([1, 2])
        with left:
            st.markdown(f"### {profile['name']}")
            st.write(f"**ชอบสถานที่:** {len(profile['likes'])} แห่ง")
            st.write(f"**เพื่อน:** {len(profile['friends'])} คน")
        with right:
            st.markdown("### สถานที่ที่ชอบ")
            if profile["likes"]:
                st.dataframe(
                    pd.DataFrame({"Location": profile["likes"]}),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("ยังไม่มีข้อมูล LIKES")

elif page == "Recommendations":
    st.subheader("✨ ระบบแนะนำสถานที่ถ่ายรูป")
    st.caption(
        "เดินกราฟ User → สถานที่ที่ชอบ → ผู้ใช้ที่มีความชอบร่วมกัน → สถานที่ใหม่ "
        "แล้วนับจำนวนเส้นทางเป็นคะแนน"
    )

    selected = user_selector("rec_user")
    top_n = st.slider("จำนวนคำแนะนำ", 1, 10, 5)
    rows = recommend_locations(selected, top_n)

    if not rows:
        st.info("ยังไม่มีสถานที่ที่สามารถแนะนำได้จากข้อมูลปัจจุบัน")
    else:
        for i, row in enumerate(rows, start=1):
            image_col, info_col = st.columns([1, 2])
            with image_col:
                image_file = row.get("image")

                if image_file:
                    image_path = BASE_DIR / image_file

                    if image_path.exists():
                        st.image(
                            str(image_path),
                            use_container_width=True
                        )
                    else:
                        st.warning(
                            f"ไม่พบไฟล์รูป: {image_path.name}"
                        )
                else:
                    st.info("ไม่มีรูปภาพ")
            with info_col:
                st.markdown(
                    """
                    <style>

                    /* ===== พื้นหลังหลัก ===== */
                    .stApp {
                        background: #FFF7FB;
                    }

                    .block-container {
                        padding-top: 1.3rem;
                        padding-bottom: 2rem;
                    }

                    /* ===== Sidebar ===== */
                    [data-testid="stSidebar"] {
                        background: #FCE7F3;
                        border-right: 1px solid #F9C5DC;
                    }

                    [data-testid="stSidebar"] h2 {
                        color: #BE5A87;
                    }

                    [data-testid="stSidebar"] .stRadio label {
                        color: #6B4657;
                        font-weight: 500;
                    }

                    [data-testid="stSidebar"] .stCaption {
                        color: #9B7183;
                    }

                    /* ===== Hero ===== */
                    .hero {
                        padding: 1.7rem 1.8rem;
                        border-radius: 24px;
                        background: linear-gradient(
                            135deg,
                            #FBCFE8 0%,
                            #F9A8D4 55%,
                            #F472B6 100%
                        );
                        color: #6B2148;
                        margin-bottom: 1.2rem;
                        box-shadow: 0 8px 24px rgba(190, 90, 135, 0.15);
                    }

                    .hero h1 {
                        margin: 0;
                        font-size: 2.15rem;
                        color: #6B2148;
                    }

                    .hero p {
                        margin: .4rem 0 0 0;
                        color: #7D385B;
                        opacity: .9;
                    }

                    /* ===== หัวข้อ ===== */
                    h1, h2, h3 {
                        color: #8F4167;
                    }

                    /* ===== Recommendation Card ===== */
                    .recommend-card {
                        padding: 1.1rem 1.2rem;
                        border: 1px solid #F7C7DC;
                        border-radius: 18px;
                        margin-bottom: .8rem;
                        background: #FFFFFF;
                        box-shadow: 0 5px 16px rgba(190, 90, 135, 0.08);
                    }

                    .recommend-card h3 {
                        color: #8F4167;
                    }

                    /* ===== Score ===== */
                    .score-pill {
                        display: inline-block;
                        padding: .25rem .65rem;
                        border-radius: 999px;
                        background: #F472B6;
                        color: white;
                        font-size: .8rem;
                        font-weight: 700;
                        box-shadow: 0 3px 8px rgba(244, 114, 182, 0.2);
                    }

                    /* ===== ตัวหนังสือรอง ===== */
                    .muted {
                        color: #9B7183;
                        font-size: .9rem;
                    }

                    /* ===== Metric Cards ===== */
                    [data-testid="stMetric"] {
                        background: #FFFFFF;
                        border: 1px solid #F7C7DC;
                        border-radius: 16px;
                        padding: 1rem;
                        box-shadow: 0 4px 14px rgba(190, 90, 135, 0.08);
                    }

                    [data-testid="stMetricLabel"] {
                        color: #9B7183;
                    }

                    [data-testid="stMetricValue"] {
                        color: #BE5A87;
                    }

                    /* ===== ปุ่ม ===== */
                    .stButton > button {
                        background: #F472B6;
                        color: white;
                        border: none;
                        border-radius: 12px;
                        padding: .55rem 1.1rem;
                        font-weight: 600;
                        transition: all .2s ease;
                    }

                    .stButton > button:hover {
                        background: #EC6AA9;
                        color: white;
                        box-shadow: 0 5px 14px rgba(244, 114, 182, 0.25);
                    }

                    /* ===== Selectbox / Slider ===== */
                    div[data-baseweb="select"] > div {
                        border-color: #F3B6D0;
                        border-radius: 12px;
                    }

                    .stSlider > div > div > div {
                        background: #F472B6;
                    }

                    /* ===== ตาราง ===== */
                    [data-testid="stDataFrame"] {
                        border: 1px solid #F7C7DC;
                        border-radius: 14px;
                        overflow: hidden;
                    }

                    /* ===== Info / Warning / Success ===== */
                    [data-testid="stAlert"] {
                        border-radius: 14px;
                    }

                    /* ===== Divider ===== */
                    hr {
                        border-color: #F7C7DC;
                    }

                    </style>
                    """,
                    unsafe_allow_html=True,
                )

        st.markdown("### ตารางผลลัพธ์")
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "User & Location":
    st.subheader("ข้อมูล User และสถานที่")

    selected = user_selector("data_user")
    profile = get_user_profile(selected)

    if profile:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### ❤️ สถานที่ที่ชอบ")
            st.write(", ".join(profile["likes"]) or "ไม่มีข้อมูล")
        with c2:
            st.markdown("### 👥 เพื่อน")
            st.write(", ".join(profile["friends"]) or "ไม่มีข้อมูล")

        st.divider()
        st.markdown("### User ที่มีความชอบร่วมกับผู้ใช้ที่เลือก")
        similar = profile["similar_users"]
        if similar:
            st.dataframe(pd.DataFrame(similar), use_container_width=True, hide_index=True)
        else:
            st.info("ยังไม่พบผู้ใช้ที่มีความชอบร่วมกัน")

elif page == "Graph Explorer":
    st.subheader("🔗 Graph Explorer")
    graph_type = st.radio(
        "เลือกกราฟ",
        ["User → Location (LIKES)", "User → User (FRIEND)", "Neighborhood"],
        horizontal=True,
    )

    if graph_type == "User → Location (LIKES)":
        rows = graph_likes()
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.markdown("### Graph")
            try:
                import networkx as nx
                import matplotlib.pyplot as plt

                G = nx.Graph()
                for row in rows:
                    G.add_node(row["user"], node_type="user")
                    G.add_node(row["location"], node_type="location")
                    G.add_edge(row["user"], row["location"])
                fig, ax = plt.subplots(figsize=(14, 9))
                pos = nx.spring_layout(G, seed=42)
                nx.draw(G, pos, with_labels=True, node_size=2500, font_size=9, ax=ax)
                ax.set_title("Photography: User Likes Location")
                st.pyplot(fig)
                plt.close(fig)
            except Exception as exc:
                st.warning(f"ไม่สามารถวาดกราฟได้: {exc}")

    elif graph_type == "User → User (FRIEND)":
        rows = graph_users()
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        try:
            import networkx as nx
            import matplotlib.pyplot as plt

            G = nx.Graph()
            for row in rows:
                G.add_edge(row["user1"], row["user2"])
            fig, ax = plt.subplots(figsize=(12, 9))
            pos = nx.spring_layout(G, seed=42)
            nx.draw(G, pos, with_labels=True, node_size=3000, font_size=10, ax=ax)
            ax.set_title("Photography: User-to-User Relationships")
            st.pyplot(fig)
            plt.close(fig)
        except Exception as exc:
            st.warning(f"ไม่สามารถวาดกราฟได้: {exc}")

    else:
        selected = user_selector("graph_user")
        rows = graph_neighborhood(selected)
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("ไม่พบเส้นทางของ User นี้")

elif page == "Cypher Examples":
    st.subheader("🧪 ตัวอย่าง Cypher จาก Colab")

    examples = {
        "ดูสถานที่ที่ User ชอบ": """
MATCH (u:User {name: $name})-[:LIKES]->(l:Location)
RETURN l.name AS location
ORDER BY location
""",
        "หา User ที่มีความชอบร่วมกัน": """
MATCH (:User {name: $name})-[:LIKES]->(l:Location)<-[:LIKES]-(other:User)
WHERE other.name <> $name
RETURN l.name AS location, collect(other.name) AS similar_users
ORDER BY location
""",
        "หาเพื่อนและสถานที่ที่เพื่อนชอบ": """
MATCH (u:User)-[:FRIEND]-(friend:User)-[:LIKES]->(l:Location)
WHERE NOT (u)-[:LIKES]->(l)
RETURN u.name AS user, friend.name AS friend, l.name AS location
ORDER BY user, friend, location
""",
    }

    selected_example = st.selectbox("เลือก Query", list(examples))
    st.code(examples[selected_example], language="cypher")

elif page == "Admin / Setup":
    st.subheader("⚙️ Admin / Setup")
    st.write("ใช้หน้านี้สำหรับสร้าง Constraint และข้อมูลตัวอย่างตาม Colab")

    if st.button("สร้าง Constraint", type="primary"):
        try:
            create_schema()
            st.success("สร้าง Constraint สำเร็จ")
        except Exception as exc:
            st.error("สร้าง Constraint ไม่สำเร็จ")
            st.exception(exc)

    if st.button("สร้างข้อมูลตัวอย่างจาก Colab"):
        try:
            seed_demo_data()
            st.success("สร้าง User, Location, LIKES และ FRIEND เรียบร้อย")
            st.rerun()
        except Exception as exc:
            st.error("สร้างข้อมูลไม่สำเร็จ")
            st.exception(exc)

    st.info(
        "ข้อมูลตัวอย่างยึดตาม Colab: 10 Users, 10 Photography Locations, "
        "21 LIKES และ 12 FRIEND relationships"
    )
