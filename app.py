                            st.rerun()
                        except Exception as exc:
                            st.error("ลบความสัมพันธ์ไม่สำเร็จ")
                            st.exception(exc)

        with delete_user_tab:
            st.markdown("### 👤 ลบคน")

            users = get_users()
            user_names = [u["name"] for u in users]

            if not user_names:
                st.info("ยังไม่มี User ให้ลบ")
            else:
                delete_user_name = st.selectbox(
                    "เลือกคนที่จะลบ",
                    user_names,
                    key="delete_user_name",
                )

                confirm_delete = st.checkbox(
                    f"ยืนยันการลบ {delete_user_name}",
                    key="confirm_delete_user",
                )

                if st.button(
                    "🗑️ ลบคน",
                    type="primary",
                    use_container_width=True,
                    key="delete_user_button",
                ):
                    if not confirm_delete:
                        st.warning(f"กรุณายืนยันการลบ {delete_user_name} ก่อน")
                    else:
                        try:
                            query(
                                """
                                MATCH (u:User {name:$name})
                                DETACH DELETE u
                                """,
                                {"name": delete_user_name},
                                write=True,
                            )
                            st.success(f"ลบ {delete_user_name} สำเร็จ")
                            st.rerun()
                        except Exception as exc:
                            st.error("ลบคนไม่สำเร็จ")
                            st.exception(exc)

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
