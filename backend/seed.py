"""
Seed script — populates the database with light mock data themed around
the Enron investigation, the most famous real-world eDiscovery matter.

Run from the backend/ directory:
    uv run python seed.py
"""

from app.core.database import SessionLocal
from app.models.group import Group
from app.models.user import User, UserRole
from app.models.workspace import Workspace

# ── Users ──────────────────────────────────────────────────────────────────────

USERS = [
    {"email": "admin@relativity.dev", "name": "Admin User", "role": UserRole.admin},
    {"email": "k.lay@enron.example", "name": "Kenneth Lay", "role": UserRole.reviewer},
    {"email": "j.skilling@enron.example", "name": "Jeffrey Skilling", "role": UserRole.reviewer},
    {"email": "s.fastow@enron.example", "name": "Sherron Fastow", "role": UserRole.reviewer},
    {"email": "l.watkins@enron.example", "name": "Sherron Watkins", "role": UserRole.viewer},
    {"email": "v.attorney@lawfirm.example", "name": "Victoria Chen", "role": UserRole.admin},
    {"email": "m.paralegal@lawfirm.example", "name": "Marcus Obi", "role": UserRole.viewer},
]

# ── Groups ─────────────────────────────────────────────────────────────────────

GROUPS = [
    {
        "name": "Senior Reviewers",
        "description": "Lead attorneys and senior review team with full document access.",
    },
    {
        "name": "Contract Reviewers",
        "description": "Contract review attorneys assigned to first-pass document review.",
    },
    {
        "name": "Read-Only",
        "description": "Clients and observers with view-only access to reviewed documents.",
    },
]

# ── Workspaces ─────────────────────────────────────────────────────────────────

WORKSPACES = [
    {
        "name": "Enron Securities Fraud – 2001",
        "description": (
            "DOJ and SEC investigation into accounting fraud and securities violations "
            "at Enron Corporation. Primary custodians: K. Lay, J. Skilling, A. Fastow."
        ),
    },
    {
        "name": "Smith v. Acme Corp – Employment",
        "description": (
            "Employment discrimination matter. Plaintiff alleges wrongful termination "
            "based on protected class. Discovery period: Jan 2019 – Dec 2022."
        ),
    },
    {
        "name": "Project Atlas – M&A Due Diligence",
        "description": (
            "Pre-acquisition document review for proposed merger. Confidential. "
            "Review scope: 3 years of financial records, contracts, and correspondence."
        ),
    },
]

# ── Group membership ───────────────────────────────────────────────────────────
# Maps group name → list of user emails to add as members.

MEMBERSHIPS = {
    "Senior Reviewers": [
        "admin@relativity.dev",
        "v.attorney@lawfirm.example",
        "k.lay@enron.example",
    ],
    "Contract Reviewers": [
        "j.skilling@enron.example",
        "s.fastow@enron.example",
    ],
    "Read-Only": [
        "l.watkins@enron.example",
        "m.paralegal@lawfirm.example",
    ],
}


def seed() -> None:
    db = SessionLocal()
    try:
        # Users
        user_map: dict[str, User] = {}
        for u in USERS:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
                user_map[u["email"]] = existing
                print(f"  skip  user  {u['email']}")
            else:
                user = User(**u)
                db.add(user)
                db.flush()  # get the id before commit
                user_map[u["email"]] = user
                print(f"  added user  {u['email']}")

        # Groups
        group_map: dict[str, Group] = {}
        for g in GROUPS:
            existing = db.query(Group).filter(Group.name == g["name"]).first()
            if existing:
                group_map[g["name"]] = existing
                print(f"  skip  group {g['name']}")
            else:
                group = Group(**g)
                db.add(group)
                db.flush()
                group_map[g["name"]] = group
                print(f"  added group {g['name']}")

        # Workspaces
        admin_user = user_map.get("admin@relativity.dev")
        for w in WORKSPACES:
            existing = db.query(Workspace).filter(Workspace.name == w["name"]).first()
            if existing:
                print(f"  skip  workspace '{w['name']}'")
            else:
                workspace = Workspace(
                    **w,
                    created_by_id=admin_user.id if admin_user else None,
                )
                db.add(workspace)
                print(f"  added workspace '{w['name']}'")

        # Memberships
        for group_name, emails in MEMBERSHIPS.items():
            group = group_map.get(group_name)
            if not group:
                continue
            for email in emails:
                user = user_map.get(email)
                if user and user not in group.members:
                    group.members.append(user)
                    print(f"  linked {email} → {group_name}")

        db.commit()
        print("\nSeed complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
