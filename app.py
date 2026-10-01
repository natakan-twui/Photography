from __future__ import annotations

import pandas as pd
import streamlit as st
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from neo4j_service import (
    create_schema,
    query,
    get_dashboard_metrics,
    get_user_profile,
    get_users,
    get_locations,
    get_user_likes,
    get_user_friends,
    create_user,
    create_friendship,
    delete_friendship,
    delete_user,
    create_location,
    delete_location,
    add_like,
    remove_like,
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

/* ===== Management Tabs ===== */
.stTabs [data-baseweb="tab-list"] {
    gap: .4rem;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 12px 12px 0 0;
    padding: .55rem 1rem;
    color: #8B6575;
}

.stTabs [aria-selected="true"] {
    color: #B6537D;
    border-bottom-color: #E88EAE;
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
        st.info("ยังไม่มีข้อมูล User กรุณาเพิ่ม User ในหน้า จัดการคน & เพื่อน")
        st.stop()
    labels = {x["name"]: x["name"] for x in users}
    chosen = st.selectbox("เลือก User", list(labels), key=key)
    return labels[chosen]


def show_location_image(image_value: str | None, caption: str | None = None) -> None:
    """แสดงรูปได้ทั้งจาก assets/locations และ URL"""
    if not image_value:
        st.info("ไม่มีรูปภาพ")
        return

    image_value = str(image_value).strip()
    if image_value.startswith(("http://", "https://")):
        st.image(image_value, caption=caption, use_container_width=True)
        return

    image_path = BASE_DIR / image_value
    if image_path.exists():
        st.image(str(image_path), caption=caption, use_container_width=True)
    else:
        st.info("ไม่พบรูปภาพ")


require_connection()

with st.sidebar:
    st.markdown("## 📷 Photography Graph")
    st.caption("Neo4j Aura + Streamlit")
    page = st.radio(
        "เมนู",
        ["Dashboard", "จัดการคน & เพื่อน", "จัดการสถานที่ถ่ายรูป & การเลือก", "กราฟความสัมพันธ์"],
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

    c1.metric("คน", m["users"])
    c2.metric("สถานที่ถ่ายรูป", m["locations"])
    c3.metric("ความชอบ", m["likes"])
    c4.metric("เพื่อน", m["friends"])

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
                            show_location_image(image_file, caption=location_name)

                            friend_text = ", ".join(friend_names)

                            # ข้อมูลการ์ด
                            st.markdown(
                                f"""
                                <div class="recommend-card">
                                    <div style="font-size:1.1rem; font-weight:700; color:#91496A;">
                                        📍 {location_name}
                                    </div>
                                    <div style="margin-top:.45rem; color:#9B7181; font-size:.9rem;">
                                        👥 เพื่อนที่ชอบสถานที่นี้:<br>
                                        <strong style="color:#91496A;">
                                            {friend_text}
                                        </strong>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

            else:
                st.info(
                    "ยังไม่มีสถานที่ใหม่ที่เพื่อนของคุณชอบ "
                    "และคุณยังไม่เคยชอบ"
                )

        else:
            st.info("ยังไม่มีข้อมูลเพื่อนสำหรับสร้างคำแนะนำ")


elif page == "จัดการคน & เพื่อน":
    st.subheader("👥 จัดการคน & เพื่อน")
    st.caption("เพิ่มคน สร้างความสัมพันธ์เพื่อน และจัดการข้อมูล User ใน Graph")

    tab_add, tab_friend, tab_delete = st.tabs(
        ["➕ เพิ่มคน", "🤝 เพิ่มความสัมพันธ์", "🗑️ ลบ"]
    )

    # =========================================================
    # เพิ่มคน
    # =========================================================
    with tab_add:
        st.markdown("### ➕ เพิ่มคน")
        st.write("เพิ่ม User ใหม่เข้าไปเป็นโหนด `User` ใน Neo4j")

        with st.form("add_user_form", clear_on_submit=True):
            new_user_name = st.text_input(
                "ชื่อคนใหม่",
                placeholder="เช่น Mew",
            ).strip()
            submit_add_user = st.form_submit_button(
                "เพิ่มคน",
                type="primary",
                use_container_width=True,
            )

        if submit_add_user:
            if not new_user_name:
                st.warning("กรุณากรอกชื่อคน")
            else:
                try:
                    if any(u["name"] == new_user_name for u in get_users()):
                        st.warning(f"มี User ชื่อ {new_user_name} อยู่แล้ว")
                    else:
                        create_user(new_user_name)
                        st.success(f"เพิ่ม {new_user_name} สำเร็จ")
                        st.rerun()
                except Exception as exc:
                    st.error("เพิ่มคนไม่สำเร็จ")
                    st.exception(exc)

    # =========================================================
    # เพิ่มความสัมพันธ์
    # =========================================================
    with tab_friend:
        st.markdown("### 🤝 เพิ่มความสัมพันธ์")

        user_names = [u["name"] for u in get_users()]
        if len(user_names) < 2:
            st.info("ต้องมี User อย่างน้อย 2 คน จึงจะสร้างความสัมพันธ์ได้")
        else:
            c1, c2 = st.columns(2)
            with c1:
                person1 = st.selectbox(
                    "คนที่ 1",
                    user_names,
                    key="manage_friend_person1",
                )
            with c2:
                person2_options = [name for name in user_names if name != person1]
                person2 = st.selectbox(
                    "คนที่ 2",
                    person2_options,
                    key="manage_friend_person2",
                )

            current_friends = get_user_friends(person1)
            st.markdown(f"### 👥 เพื่อนของ {person1} ตอนนี้")

            if current_friends:
                friend_cols = st.columns(min(len(current_friends), 4))
                for i, friend in enumerate(current_friends):
                    with friend_cols[i % len(friend_cols)]:
                        st.markdown(
                            f"""
                            <div class="recommend-card" style="text-align:center;">
                                <div style="font-size:1.8rem;">👤</div>
                                <strong>{friend}</strong>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            else:
                st.info(f"{person1} ยังไม่มีเพื่อน")

            if person2 in current_friends:
                st.warning(f"{person1} และ {person2} เป็นเพื่อนกันอยู่แล้ว")

            if st.button(
                "🤝 เชื่อมเป็นเพื่อนกัน",
                type="primary",
                use_container_width=True,
                key="add_friend_button",
            ):
                try:
                    if person1 == person2:
                        st.warning("ไม่สามารถเชื่อมคนเดียวกันเป็นเพื่อนได้")
                    elif person2 in current_friends:
                        st.warning(f"{person1} และ {person2} เป็นเพื่อนกันอยู่แล้ว")
                    else:
                        create_friendship(person1, person2)
                        st.success(f"เชื่อม {person1} และ {person2} เป็นเพื่อนกันแล้ว")
                        st.rerun()
                except Exception as exc:
                    st.error("เพิ่มความสัมพันธ์ไม่สำเร็จ")
                    st.exception(exc)

    # =========================================================
    # ลบ
    # =========================================================
    with tab_delete:
        delete_relation_tab, delete_user_tab = st.tabs(
            ["🗑️ ลบความสัมพันธ์", "👤 ลบคน"]
        )

        with delete_relation_tab:
            st.markdown("### 🗑️ ลบความสัมพันธ์เพื่อน")
            user_names = [u["name"] for u in get_users()]

            if len(user_names) < 2:
                st.info("ยังไม่มีข้อมูลเพียงพอสำหรับลบความสัมพันธ์")
            else:
                person1 = st.selectbox(
                    "เลือกคน",
                    user_names,
                    key="delete_friend_person1",
                )
                current_friends = get_user_friends(person1)

                if not current_friends:
                    st.info(f"{person1} ยังไม่มีความสัมพันธ์เพื่อน")
                else:
                    friend_to_remove = st.selectbox(
                        "เลือกเพื่อนที่ต้องการลบความสัมพันธ์",
                        current_friends,
                        key="delete_friend_person2",
                    )
                    if st.button(
                        "🗑️ ลบความสัมพันธ์",
                        type="primary",
                        use_container_width=True,
                        key="delete_friend_button",
                    ):
                        try:
                            delete_friendship(person1, friend_to_remove)
                            st.success(
                                f"ลบความสัมพันธ์ระหว่าง {person1} และ {friend_to_remove} แล้ว"
                            )
                            st.rerun()
                        except Exception as exc:
                            st.error("ลบความสัมพันธ์ไม่สำเร็จ")
                            st.exception(exc)

        with delete_user_tab:
            st.markdown("### 👤 ลบคน")
            st.warning("การลบคนจะลบความสัมพันธ์ FRIEND และ LIKES ของคนนั้นด้วย")
            user_names = [u["name"] for u in get_users()]

            if not user_names:
                st.info("ยังไม่มี User ให้ลบ")
            else:
                delete_name = st.selectbox(
                    "เลือกคนที่จะลบ",
                    user_names,
                    key="delete_user_name",
                )
                confirm = st.checkbox(
                    f"ฉันยืนยันการลบ {delete_name}",
                    key=f"confirm_delete_{delete_name}",
                )

                if st.button(
                    "🗑️ ลบคน",
                    type="primary",
                    use_container_width=True,
                    key="delete_user_button",
                ):
                    if not confirm:
                        st.warning("กรุณาติ๊กยืนยันก่อนลบ")
                    else:
                        try:
                            delete_user(delete_name)
                            st.success(f"ลบ {delete_name} สำเร็จ")
                            st.rerun()
                        except Exception as exc:
                            st.error("ลบคนไม่สำเร็จ")
                            st.exception(exc)


elif page == "จัดการสถานที่ถ่ายรูป & การเลือก":
    st.subheader("📍 จัดการสถานที่ถ่ายรูป & การเลือก")
    st.caption("เพิ่มสถานที่ จัดการการเลือก ❤️ และลบข้อมูล Location")

    tab_location, tab_likes, tab_delete_location = st.tabs(
        ["📍 เพิ่มสถานที่", "❤️ จัดการการเลือก", "🗑️ ลบ"]
    )

    # =========================================================
    # เพิ่มสถานที่
    # =========================================================
    with tab_location:
        st.markdown("### 📍 เพิ่มสถานที่ถ่ายรูป")
        st.write("เพิ่ม Location ใหม่เป็นโหนด `Location` ใน Neo4j")

        with st.form("add_location_form", clear_on_submit=True):
            new_location_name = st.text_input(
                "ชื่อสถานที่",
                placeholder="เช่น Siam Square",
            ).strip()
            new_location_image = st.text_input(
                "URL รูปภาพ (ไม่บังคับ)",
                placeholder="https://...",
            ).strip()
            submit_add_location = st.form_submit_button(
                "เพิ่มสถานที่",
                type="primary",
                use_container_width=True,
            )

        if submit_add_location:
            if not new_location_name:
                st.warning("กรุณากรอกชื่อสถานที่")
            else:
                try:
                    if any(l["name"] == new_location_name for l in get_locations()):
                        st.warning(f"มีสถานที่ชื่อ {new_location_name} อยู่แล้ว")
                    else:
                        create_location(new_location_name, new_location_image)
                        st.success(f"เพิ่มสถานที่ {new_location_name} สำเร็จ")
                        st.rerun()
                except Exception as exc:
                    st.error("เพิ่มสถานที่ไม่สำเร็จ")
                    st.exception(exc)

        st.divider()
        st.markdown("### 📋 สถานที่ในระบบ")
        locations = get_locations()
        if locations:
            st.dataframe(
                pd.DataFrame(locations).rename(columns={"name": "สถานที่", "image": "รูปภาพ"}),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("ยังไม่มีสถานที่")

    # =========================================================
    # จัดการ LIKES
    # =========================================================
    with tab_likes:
        st.markdown("### ❤️ จัดการการเลือกสถานที่")
        st.caption("สร้างหรือลบความสัมพันธ์ User → Location ด้วย `LIKES`")

        user_names = [u["name"] for u in get_users()]
        location_names = [l["name"] for l in get_locations()]

        if not user_names or not location_names:
            st.info("ต้องมีทั้ง User และสถานที่ก่อนจึงจะจัดการการเลือกได้")
        else:
            c1, c2 = st.columns(2)
            with c1:
                like_user = st.selectbox("เลือก User", user_names, key="like_user")
            with c2:
                like_location = st.selectbox(
                    "เลือกสถานที่",
                    location_names,
                    key="like_location",
                )

            current_likes = get_user_likes(like_user)
            st.markdown(f"### ❤️ สถานที่ที่ {like_user} เลือก")

            if current_likes:
                like_cols = st.columns(min(len(current_likes), 4))
                for i, location in enumerate(current_likes):
                    with like_cols[i % len(like_cols)]:
                        st.markdown(
                            f"""
                            <div class="recommend-card" style="text-align:center;">
                                <div style="font-size:1.6rem;">📍</div>
                                <strong>{location}</strong>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            else:
                st.info(f"{like_user} ยังไม่มีสถานที่ที่เลือก")

            if like_location in current_likes:
                st.warning(f"{like_user} เลือก {like_location} อยู่แล้ว")
            else:
                if st.button(
                    "❤️ เพิ่มการเลือก",
                    type="primary",
                    use_container_width=True,
                    key="add_like_button",
                ):
                    try:
                        add_like(like_user, like_location)
                        st.success(f"เพิ่ม {like_user} → {like_location} แล้ว")
                        st.rerun()
                    except Exception as exc:
                        st.error("เพิ่มการเลือกไม่สำเร็จ")
                        st.exception(exc)

            st.divider()
            if current_likes:
                remove_location = st.selectbox(
                    "เลือกสถานที่ที่ต้องการยกเลิกการเลือก",
                    current_likes,
                    key="remove_like_location",
                )
                if st.button(
                    "💔 ยกเลิกการเลือก",
                    use_container_width=True,
                    key="remove_like_button",
                ):
                    try:
                        remove_like(like_user, remove_location)
                        st.success(f"ยกเลิก {like_user} → {remove_location} แล้ว")
                        st.rerun()
                    except Exception as exc:
                        st.error("ยกเลิกการเลือกไม่สำเร็จ")
                        st.exception(exc)

    # =========================================================
    # ลบ Location
    # =========================================================
    with tab_delete_location:
        st.markdown("### 🗑️ ลบสถานที่ถ่ายรูป")
        st.warning("การลบสถานที่จะลบความสัมพันธ์ LIKES ที่เชื่อมกับสถานที่นั้นด้วย")

        location_names = [l["name"] for l in get_locations()]
        if not location_names:
            st.info("ยังไม่มีสถานที่ให้ลบ")
        else:
            delete_location_name = st.selectbox(
                "เลือกสถานที่ที่จะลบ",
                location_names,
                key="delete_location_name",
            )
            confirm_location = st.checkbox(
                f"ฉันยืนยันการลบ {delete_location_name}",
                key=f"confirm_delete_location_{delete_location_name}",
            )

            if st.button(
                "🗑️ ลบสถานที่",
                type="primary",
                use_container_width=True,
                key="delete_location_button",
            ):
                if not confirm_location:
                    st.warning("กรุณาติ๊กยืนยันก่อนลบ")
                else:
                    try:
                        delete_location(delete_location_name)
                        st.success(f"ลบ {delete_location_name} สำเร็จ")
                        st.rerun()
                    except Exception as exc:
                        st.error("ลบสถานที่ไม่สำเร็จ")
                        st.exception(exc)


elif page == "กราฟความสัมพันธ์":
    st.subheader("🕸️ กราฟความสัมพันธ์")
    st.caption("ดูโครงสร้าง User, Location, LIKES และ FRIEND ที่เก็บอยู่ใน Neo4j")

    graph_tab_all, graph_tab_likes, graph_tab_friends, graph_tab_user = st.tabs(
        ["🌐 ภาพรวม", "❤️ User → Location", "👥 User ↔ User", "🧭 รายบุคคล"]
    )

    with graph_tab_all:
        st.markdown("### 🌐 ภาพรวมความสัมพันธ์")
        rows_likes = graph_likes()
        rows_friends = graph_users()

        m = get_dashboard_metrics()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("คน", m["users"])
        c2.metric("สถานที่", m["locations"])
        c3.metric("LIKES", m["likes"])
        c4.metric("FRIEND", m["friends"])

        try:
            import networkx as nx
            import matplotlib.pyplot as plt

            G = nx.Graph()
            for row in rows_likes:
                G.add_node(row["user"], node_type="user")
                G.add_node(row["location"], node_type="location")
                G.add_edge(row["user"], row["location"], relation="LIKES")
            for row in rows_friends:
                G.add_node(row["user1"], node_type="user")
                G.add_node(row["user2"], node_type="user")
                G.add_edge(row["user1"], row["user2"], relation="FRIEND")

            if G.number_of_nodes():
                fig, ax = plt.subplots(figsize=(14, 9))
                pos = nx.spring_layout(G, seed=42)
                nx.draw(
                    G,
                    pos,
                    with_labels=True,
                    node_size=2200,
                    font_size=9,
                    ax=ax,
                )
                ax.set_title("Photography Location Recommender Graph")
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.info("ยังไม่มีข้อมูลสำหรับวาดกราฟ")
        except Exception as exc:
            st.warning(f"ไม่สามารถวาดกราฟได้: {exc}")

    with graph_tab_likes:
        st.markdown("### ❤️ User → Location")
        rows = graph_likes()
        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("ยังไม่มีความสัมพันธ์ LIKES")

    with graph_tab_friends:
        st.markdown("### 👥 User ↔ User")
        rows = graph_users()
        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("ยังไม่มีความสัมพันธ์ FRIEND")

    with graph_tab_user:
        st.markdown("### 🧭 ดูความสัมพันธ์ของ User ที่เลือก")
        selected = user_selector("graph_user")
        rows = graph_neighborhood(selected)
        if rows:
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("ไม่พบความสัมพันธ์ของ User นี้")

