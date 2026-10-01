from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl


USERS = [
    "Pim", "Beam", "Mew", "Film", "Nina",
    "Earth", "Praew", "Win", "View", "Mark"
]

LOCATIONS = [
    "ICONSIAM", "Talad Noi", "Asiatique The Riverfront",
    "Benjakitti Park", "Chatuchak Weekend Market",
    "The Commons Thonglor", "Wat Arun", "Yaowarat",
    "Bangkok Art and Culture Centre", "Ancient City"
]

LIKES = [
    ("Pim", "ICONSIAM"), ("Pim", "Talad Noi"),
    ("Beam", "ICONSIAM"), ("Beam", "Talad Noi"), ("Beam", "Yaowarat"),
    ("Mew", "Talad Noi"), ("Mew", "Bangkok Art and Culture Centre"),
    ("Film", "Yaowarat"), ("Film", "Chatuchak Weekend Market"),
    ("Nina", "Benjakitti Park"), ("Nina", "The Commons Thonglor"),
    ("Earth", "Benjakitti Park"), ("Earth", "The Commons Thonglor"),
    ("Earth", "Asiatique The Riverfront"),
    ("Praew", "Wat Arun"), ("Praew", "ICONSIAM"),
    ("Win", "Wat Arun"), ("Win", "Yaowarat"),
    ("View", "Chatuchak Weekend Market"), ("View", "Ancient City"),
    ("Mark", "Ancient City"), ("Mark", "Asiatique The Riverfront"),
]



LOCATION_IMAGES = {
    "ICONSIAM": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1200&q=80",
    "Talad Noi": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
    "Asiatique The Riverfront": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?auto=format&fit=crop&w=1200&q=80",
    "Benjakitti Park": "https://images.unsplash.com/photo-1470214304380-aadaedcfff1b?auto=format&fit=crop&w=1200&q=80",
    "Chatuchak Weekend Market": "https://images.unsplash.com/photo-1523731407965-2430cd12f5e4?auto=format&fit=crop&w=1200&q=80",
    "The Commons Thonglor": "https://images.unsplash.com/photo-1554118811-1e0d58224f24?auto=format&fit=crop&w=1200&q=80",
    "Wat Arun": "https://images.unsplash.com/photo-1563492065599-3520f775eeed?auto=format&fit=crop&w=1200&q=80",
    "Yaowarat": "https://images.unsplash.com/photo-1528181304800-259b08848526?auto=format&fit=crop&w=1200&q=80",
    "Bangkok Art and Culture Centre": "https://images.unsplash.com/photo-1549490349-8643362247b5?auto=format&fit=crop&w=1200&q=80",
    "Ancient City": "https://images.unsplash.com/photo-1506665531195-3566af2b4dfa?auto=format&fit=crop&w=1200&q=80",
}

FRIENDSHIPS = [
    ("Pim", "Beam"),
    ("Pim", "Mew"),
    ("Beam", "Mew"),
    ("Beam", "Film"),
    ("Mew", "Nina"),
    ("Film", "Win"),
    ("Nina", "Earth"),
    ("Earth", "Praew"),
    ("Praew", "Win"),
    ("Win", "View"),
    ("View", "Mark"),
    ("Mark", "Pim"),
]


def _config() -> tuple[str, str, str, str]:
    cfg = st.secrets["neo4j"]
    return (
        cfg["uri"],
        cfg["username"],
        cfg["password"],
        cfg.get("database", "neo4j"),
    )


@st.cache_resource(show_spinner=False)
def get_driver():
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def query(
    cypher: str,
    parameters: dict[str, Any] | None = None,
    *,
    write: bool = False,
) -> list[dict[str, Any]]:
    _, _, _, database = _config()
    records, _, _ = get_driver().execute_query(
        cypher,
        parameters_=parameters or {},
        database_=database,
        routing_=RoutingControl.WRITE if write else RoutingControl.READ,
    )
    return [record.data() for record in records]


def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


def create_schema() -> None:
    statements = [
        "CREATE CONSTRAINT user_name_unique IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE",
        "CREATE CONSTRAINT location_name_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
    ]
    for stmt in statements:
        query(stmt, write=True)


def seed_demo_data() -> None:
    """Create the exact sample data used in the supplied Colab notebook."""
    create_schema()

    query(
        "UNWIND $names AS name MERGE (:User {name:name})",
        {"names": USERS},
        write=True,
    )
    location_rows = [
        {"name": name, "image": LOCATION_IMAGES.get(name, "")}
        for name in LOCATIONS
    ]
    query(
        """
        UNWIND $rows AS row
        MERGE (l:Location {name: row.name})
        SET l.image = row.image
        """,
        {"rows": location_rows},
        write=True,
    )

    like_rows = [{"user": u, "location": l} for u, l in LIKES]
    query(
        """
        UNWIND $rows AS row
        MATCH (u:User {name: row.user}), (l:Location {name: row.location})
        MERGE (u)-[:LIKES]->(l)
        """,
        {"rows": like_rows},
        write=True,
    )

    friend_rows = [{"user1": a, "user2": b} for a, b in FRIENDSHIPS]
    query(
        """
        UNWIND $rows AS row
        MATCH (u1:User {name: row.user1})
        MATCH (u2:User {name: row.user2})
        MERGE (u1)-[:FRIEND]-(u2)
        """,
        {"rows": friend_rows},
        write=True,
    )


def get_users() -> list[dict[str, Any]]:
    return query(
        "MATCH (u:User) RETURN u.name AS name ORDER BY name"
    )


def get_locations() -> list[dict[str, Any]]:
    return query(
        "MATCH (l:Location) RETURN l.name AS name, l.image AS image ORDER BY name"
    )


def get_dashboard_metrics() -> dict[str, int]:
    rows = query(
        """
        MATCH (u:User) WITH count(u) AS users
        MATCH (l:Location) WITH users, count(l) AS locations
        OPTIONAL MATCH ()-[like:LIKES]->()
        WITH users, locations, count(like) AS likes
        OPTIONAL MATCH ()-[friend:FRIEND]-()
        RETURN users, locations, likes, count(DISTINCT friend) AS friends
        """
    )
    if not rows:
        return {"users": 0, "locations": 0, "likes": 0, "friends": 0}
    return rows[0]


def get_user_likes(name: str) -> list[str]:
    rows = query(
        """
        MATCH (u:User {name:$name})-[:LIKES]->(l:Location)
        RETURN l.name AS location
        ORDER BY location
        """,
        {"name": name},
    )
    return [r["location"] for r in rows]


def get_user_friends(name: str) -> list[str]:
    rows = query(
        """
        MATCH (u:User {name:$name})-[:FRIEND]-(friend:User)
        RETURN friend.name AS friend
        ORDER BY friend
        """,
        {"name": name},
    )
    return [r["friend"] for r in rows]


def get_user_profile(name: str) -> dict[str, Any] | None:
    users = query(
        "MATCH (u:User {name:$name}) RETURN u.name AS name",
        {"name": name},
    )
    if not users:
        return None

    likes = get_user_likes(name)
    friends = get_user_friends(name)

    similar = query(
        """
        MATCH (:User {name:$name})-[:LIKES]->(l:Location)<-[:LIKES]-(other:User)
        WHERE other.name <> $name
        RETURN l.name AS location, collect(other.name) AS similar_users
        ORDER BY location
        """,
        {"name": name},
    )

    return {
        "name": name,
        "likes": likes,
        "friends": friends,
        "similar_users": similar,
    }



def create_user(name: str) -> None:
    name = name.strip()
    if not name:
        raise ValueError("ชื่อ User ต้องไม่ว่าง")
    create_schema()
    query(
        "MERGE (:User {name:$name})",
        {"name": name},
        write=True,
    )


def create_friendship(person1: str, person2: str) -> None:
    if person1 == person2:
        raise ValueError("ไม่สามารถสร้างความสัมพันธ์กับตัวเองได้")
    query(
        """
        MATCH (a:User {name:$person1}), (b:User {name:$person2})
        MERGE (a)-[:FRIEND]-(b)
        """,
        {"person1": person1, "person2": person2},
        write=True,
    )


def delete_friendship(person1: str, person2: str) -> None:
    query(
        """
        MATCH (a:User {name:$person1})-[r:FRIEND]-(b:User {name:$person2})
        DELETE r
        """,
        {"person1": person1, "person2": person2},
        write=True,
    )


def delete_user(name: str) -> None:
    query(
        "MATCH (u:User {name:$name}) DETACH DELETE u",
        {"name": name},
        write=True,
    )


def create_location(name: str, image: str = "") -> None:
    name = name.strip()
    image = image.strip()
    if not name:
        raise ValueError("ชื่อสถานที่ต้องไม่ว่าง")
    create_schema()
    query(
        """
        MERGE (l:Location {name:$name})
        SET l.image = $image
        """,
        {"name": name, "image": image},
        write=True,
    )


def delete_location(name: str) -> None:
    query(
        "MATCH (l:Location {name:$name}) DETACH DELETE l",
        {"name": name},
        write=True,
    )


def add_like(user: str, location: str) -> None:
    query(
        """
        MATCH (u:User {name:$user}), (l:Location {name:$location})
        MERGE (u)-[:LIKES]->(l)
        """,
        {"user": user, "location": location},
        write=True,
    )


def remove_like(user: str, location: str) -> None:
    query(
        """
        MATCH (u:User {name:$user})-[r:LIKES]->(l:Location {name:$location})
        DELETE r
        """,
        {"user": user, "location": location},
        write=True,
    )

def recommend_locations(target_user: str, top_n: int | None = None) -> list[dict[str, Any]]:
    exists = query(
        "MATCH (u:User {name:$name}) RETURN u.name AS name",
        {"name": target_user},
    )
    if not exists:
        raise ValueError(f"ไม่พบผู้ใช้: {target_user}")
    if top_n is not None and (not isinstance(top_n, int) or top_n <= 0):
        raise ValueError("top_n ต้องเป็นจำนวนเต็มที่มากกว่า 0 หรือเป็น None")

    rows = query(
        """
        MATCH (target:User {name: $target_user})-[:LIKES]->(liked:Location)
        MATCH (similar:User)-[:LIKES]->(liked)
        WHERE similar <> target
        MATCH (similar)-[:LIKES]->(recommended:Location)
        WHERE NOT (target)-[:LIKES]->(recommended)
        RETURN recommended.name AS location,
               recommended.image AS image,
               count(*) AS score
        ORDER BY score DESC, location ASC
        """,
        {"target_user": target_user},
    )
    return rows[:top_n] if top_n is not None else rows


def graph_likes() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User)-[:LIKES]->(l:Location)
        RETURN u.name AS user, l.name AS location
        ORDER BY user, location
        """
    )


def graph_users() -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u1:User)-[:FRIEND]-(u2:User)
        RETURN DISTINCT u1.name AS user1, u2.name AS user2
        ORDER BY user1, user2
        """
    )


def graph_neighborhood(name: str, limit: int = 50) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:User {name:$name})
        OPTIONAL MATCH p=(u)-[:FRIEND|LIKES*1..2]-(x)
        WITH collect(p)[0..$limit] AS paths
        UNWIND paths AS p
        UNWIND relationships(p) AS r
        WITH DISTINCT startNode(r) AS s, r, endNode(r) AS t
        RETURN coalesce(s.name, '') AS source,
               type(r) AS relationship,
               coalesce(t.name, '') AS target
        LIMIT $limit
        """,
        {"name": name, "limit": int(limit)},
    )
