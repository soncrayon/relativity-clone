"""
Workspaces API — CRUD for the top-level case/matter container.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.workspace import Workspace

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


class WorkspaceCreate(BaseModel):
    """Fields required to create a new workspace."""
    name: str
    description: str | None = None
    created_by_id: int | None = None


# ── endpoints ──────────────────────────────────────────────────────────────────

@router.get("/")
def list_workspaces(db: Session = Depends(get_db)):
    """Return all workspaces. The frontend uses this to populate the Workspaces table."""
    workspaces = db.query(Workspace).order_by(Workspace.created_at.desc()).all()
    return [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "created_by_id": w.created_by_id,
            "created_at": w.created_at,
        }
        for w in workspaces
    ]


@router.post("/", status_code=201)
def create_workspace(body: WorkspaceCreate, db: Session = Depends(get_db)):
    """Create a new workspace (case/matter)."""
    existing = db.query(Workspace).filter(Workspace.name == body.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"A workspace named '{body.name}' already exists.")

    workspace = Workspace(
        name=body.name,
        description=body.description,
        created_by_id=body.created_by_id,
    )
    db.add(workspace)
    db.commit()
    db.refresh(workspace)

    return {"id": workspace.id, "name": workspace.name, "description": workspace.description, "created_at": workspace.created_at}


@router.get("/{workspace_id}")
def get_workspace(workspace_id: int, db: Session = Depends(get_db)):
    """Return a single workspace by ID."""
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    return {
        "id": workspace.id,
        "name": workspace.name,
        "description": workspace.description,
        "created_by_id": workspace.created_by_id,
        "created_at": workspace.created_at,
    }


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(workspace_id: int, db: Session = Depends(get_db)):
    """
    Delete a workspace and all its documents (cascade is handled by the DB).
    Returns 204 No Content on success — no body, just a confirmation the delete happened.
    """
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found.")
    db.delete(workspace)
    db.commit()
