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
      /* ===== Pastel Pink Theme ===== */

.stApp {
    background-color: #FFF8FB;
}

/* Main content */
.block-container {
    padding-top: 1.3rem;
    padding-bottom: 2rem;
}

/* ===== Sidebar ===== */

[data-testid="stSidebar"] {
    background: linear-gradient(
        180deg,
        #FFF0F6 0%,
        #FCE7F3 100%
    );
    border-right: 1px solid #F5C6D9;
}

[data-testid="stSidebar"] h2 {
    color: #9B4F72;
}

[data-testid="stSidebar"] p {
    color: #8B6575;
}

/* ===== Hero ===== */

.hero {
    padding: 1.5rem 1.7rem;
    border-radius: 22px;
    background: linear-gradient(
        120deg,
        #FBCFE8 0%,
        #F9A8D4 55%,
        #FCE7F3 100%
    );
    color: #713B55;
    margin-bottom: 1rem;
    border: 1px solid #F4BCD3;
    box-shadow: 0 6px 18px rgba(190, 100, 135, 0.10);
}

.hero h1 {
    margin: 0;
    font-size: 2.15rem;
    color: #713B55;
}

.hero p {
    opacity: .9;
    margin: .35rem 0 0 0;
    color: #814A63;
}

/* ===== Headings ===== */

h1, h2, h3 {
    color: #91496A;
}

/* ===== Metric ===== */

[data-testid="stMetric"] {
    background: #FFFFFF;
    border: 1px solid #F3C4D6;
    border-radius: 16px;
    padding: 1rem;
    box-shadow: 0 4px 12px rgba(190, 100, 135, 0.07);
}

[data-testid="stMetricLabel"] {
    color: #9A7181;
}

[data-testid="stMetricValue"] {
    color: #B6537D;
}

/* ===== Recommendation Card ===== */

.recommend-card {
    padding: 1rem 1.1rem;
    border: 1px solid #F3C4D6;
    border-radius: 16px;
    margin-bottom: .75rem;
    background: #FFFFFF;
    box-shadow: 0 4px 14px rgba(190, 100, 135, 0.08);
}

/* ===== Score ===== */

.score-pill {
    display: inline-block;
    padding: .2rem .55rem;
    border-radius: 999px;
    background: #E88EAE;
    color: #FFFFFF;
    font-size: .8rem;
    font-weight: 700;
}

/* ===== Muted Text ===== */

.muted {
    opacity: .72;
    font-size: .9rem;
    color: #9B7181;
}

/* ===== Buttons ===== */

.stButton > button {
    border-radius: 12px;
    border: 1px solid #E8A6BE;
    background: #F4A6C1;
    color: #FFFFFF;
    font-weight: 600;
}

.stButton > button:hover {
    background: #E88EAE;
    border-color: #E88EAE;
    color: #FFFFFF;
}

/* ===== Selectbox ===== */

[data-baseweb="select"] > div {
    border-color: #EFC0D2;
    border-radius: 12px;
}

/* ===== DataFrame ===== */

[data-testid="stDataFrame"] {
    border: 1px solid #F3C4D6;
    border-radius: 14px;
    overflow: hidden;
}

/* ===== Divider ===== */

hr {
    border-color: #F3C4D6;
}

/* ===== Alert ===== */

[data-testid="stAlert"] {
    border-radius: 14px;
}
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
    st.subheader("📊 Dashboard")

    # ===== Graph Overview =====
    m = get_dashboard_metrics()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Users", m["users"])
    c2.metric("Locations", m["locations"])
    c3.metric("LIKES", m["likes"])
    c4.metric("FRIEND", m["friends"])

    st.divider()

    # ===== Select User =====
    selected = user_selector("dash_user")
    profile = get_user_profile(selected)

    if profile:

        # ===== Selected User =====
        st.markdown(f"### 👤 {selected}")

        user_col1, user_col2 = st.columns(2)

        with user_col1:
            st.markdown("**❤️ สถานที่ที่ชอบ**")
            st.write(f"{len(profile['likes'])} แห่ง")

        with user_col2:
            st.markdown("**👥 เพื่อน**")
            st.write(f"{len(profile['friends'])} คน")

        st.divider()

        # ===== Friends =====
        st.markdown("### 👥 เพื่อนของคุณ")

        friends = get_user_friends(selected)

        if friends:
            friend_cols = st.columns(min(len(friends), 4))

            for i, friend in enumerate(friends):
                with friend_cols[i % len(friend_cols)]:
                    st.markdown(
                        f"""
                        <div class="recommend-card" style="text-align:center;">
                            <div style="font-size:2rem;">👤</div>
                            <strong>{friend}</strong>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.info("ผู้ใช้นี้ยังไม่มีเพื่อน")

        st.divider()

        # ===== Recommended Locations from Friends =====
        st.markdown("### ✨ สถานที่ที่แนะนำจากเพื่อน")

        if friends:

            # เก็บสถานที่ + รายชื่อเพื่อนที่ชอบสถานที่นั้น
            recommended = {}

            for friend in friends:
                friend_likes = get_user_likes(friend)

                for location in friend_likes:

                    # ไม่แนะนำสถานที่ที่ User เลือกชอบอยู่แล้ว
                    if location not in profile["likes"]:

                        if location not in recommended:
                            recommended[location] = []

                        recommended[location].append(friend)

            # เรียงสถานที่ที่มีเพื่อนชอบมากที่สุดก่อน
            recommended = dict(
                sorted(
                    recommended.items(),
                    key=lambda item: (-len(item[1]), item[0])
                )
            )

            # เอาข้อมูลรูปภาพของ Location
            locations = get_locations()

            image_map = {
                location["name"]: location.get("image")
                for location in locations
            }

            if recommended:

                # แสดงสูงสุด 6 สถานที่
                recommended_items = list(recommended.items())[:6]

                for row_start in range(0, len(recommended_items), 3):

                    row_items = recommended_items[row_start:row_start + 3]
                    cols = st.columns(3)

                    for col, (location_name, friend_names) in zip(
                        cols, row_items
                    ):

                        with col:

                            # รูปสถานที่
                            image_file = image_map.get(location_name)

                            if image_file:
                                image_path = BASE_DIR / image_file

                                if image_path.exists():
                                    st.image(
                                        str(image_path),
                                        use_container_width=True
                                    )
                                else:
                                    st.info("ไม่พบรูปภาพ")
                            else:
                                st.info("ไม่มีรูปภาพ")

                            friend_text = ", ".join(friend_names)

                            st.markdown(f"### 📍 {location_name}")
                            st.markdown(
                                f"👥 **เพื่อนที่ชอบสถานที่นี้:** {friend_text}"
                            )

            else:
                st.info(
                    "ยังไม่มีสถานที่ใหม่ที่เพื่อนของคุณชอบ "
                    "และคุณยังไม่เคยชอบ"
                )

        else:
            st.info("ยังไม่มีข้อมูลเพื่อนสำหรับสร้างคำแนะนำ")


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
                    f"""
                    <div class="recommend-card">
                        <span class="score-pill">อันดับ {i} · Score {row['score']}</span>
                        <h3 style="margin:.55rem 0 .2rem 0;">📍 {row['location']}</h3>
                        <div class="muted">
                            สถานที่นี้เชื่อมโยงผ่านผู้ใช้ที่มีความชอบร่วมกัน
                        </div>
                    </div>
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
