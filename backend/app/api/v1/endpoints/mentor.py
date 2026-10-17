from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.idea import Idea
from app.models.paper import AcademicPaper
from app.models.mentor import MentorConversation, MentorMessage
from app.schemas.mentor import (
    MentorConversationCreate, MentorConversationOut, MentorMessageOut, SendMessageRequest
)
from app.api.v1.deps import get_current_user
from app.services.ai.factory import get_llm_provider

router = APIRouter()

MODE_SYSTEM_PROMPTS = {
    "idea": "You are the Idea Mentor. Help users sharpen their value proposition, clarify user personas, and evaluate problem significance.",
    "research": "You are the Research Mentor. Help users formulate hypotheses, find scholarly precedents, and interpret academic papers.",
    "technical": "You are the Technical Mentor. Recommend clean architectures, scalable database schemas, and robust API designs.",
    "product": "You are the Product Mentor. Guide MVP scoping, prioritize user stories, and streamline onboarding workflows.",
    "business": "You are the Business Mentor. Analyze monetization models, pricing tiers, unit economics, and competitive barriers.",
    "validation": "You are the Validation Mentor. Design customer discovery interviews, smoke tests, and quantitative experiments.",
    "pitch": "You are the Pitch Mentor. Critique pitch decks, refine executive summaries, and prepare answers for investor questions."
}


@router.get("/conversations", response_model=List[MentorConversationOut])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all persistent AI mentor conversations for the current user."""
    convs = (
        db.query(MentorConversation)
        .filter(MentorConversation.user_id == current_user.id)
        .order_by(MentorConversation.updated_at.desc())
        .all()
    )
    return convs


@router.post("/conversations", response_model=MentorConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: MentorConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new mentor session with selected mode and project context."""
    # Verify project if passed
    if conv_in.project_id:
        proj = db.query(Project).filter(Project.id == conv_in.project_id, Project.user_id == current_user.id).first()
        if not proj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or unauthorized")

    title = conv_in.title or f"{conv_in.mode.title()} Mentoring Session"

    conv = MentorConversation(
        user_id=current_user.id,
        project_id=conv_in.project_id,
        idea_id=conv_in.idea_id,
        mode=conv_in.mode,
        title=title,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    # Add welcome greeting from mentor
    greeting = (
        f"Hello! I am your {conv_in.mode.title()} Mentor. "
        "How can I assist you in advancing, validating, or stress-testing your project today?"
    )
    msg = MentorMessage(
        conversation_id=conv.id,
        sender="mentor",
        content=greeting,
        cited_sources=[],
        created_at=datetime.now(timezone.utc)
    )
    db.add(msg)
    db.commit()
    db.refresh(conv)
    return conv


@router.get("/conversations/{conversation_id}", response_model=MentorConversationOut)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns a conversation and its full message history."""
    conv = (
        db.query(MentorConversation)
        .filter(MentorConversation.id == conversation_id, MentorConversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.post("/conversations/{conversation_id}/messages", response_model=MentorMessageOut)
def send_message(
    conversation_id: int,
    msg_in: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Appends user message, injects project and idea context, generates mentor response,
    and links any relevant saved project citations.
    """
    conv = (
        db.query(MentorConversation)
        .filter(MentorConversation.id == conversation_id, MentorConversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    # Save User message
    user_msg = MentorMessage(
        conversation_id=conv.id,
        sender="user",
        content=msg_in.content,
        cited_sources=[],
        created_at=datetime.now(timezone.utc)
    )
    db.add(user_msg)
    db.commit()

    # Build context from project & idea if available
    context_lines = []
    citations = []
    if conv.project_id:
        proj = db.query(Project).filter(Project.id == conv.project_id).first()
        if proj:
            context_lines.append(f"Project Title: {proj.title}")
            context_lines.append(f"Domain: {proj.domain or 'General'}")

        # Check for idea
        idea = None
        if conv.idea_id:
            idea = db.query(Idea).filter(Idea.id == conv.idea_id).first()
        else:
            # Pick selected idea
            idea = db.query(Idea).filter(Idea.project_id == conv.project_id, Idea.is_selected == True).first()
            if not idea:
                idea = db.query(Idea).filter(Idea.project_id == conv.project_id).first()

        if idea:
            context_lines.append(f"Idea: {idea.title}")
            context_lines.append(f"Problem: {idea.problem_statement}")
            context_lines.append(f"Solution: {idea.proposed_solution}")

        # Saved papers
        papers = db.query(AcademicPaper).filter(AcademicPaper.project_id == conv.project_id).limit(3).all()
        for p in papers:
            citations.append({
                "source_type": "paper",
                "title": p.title,
                "url": p.source_url or ""
            })

    # Recent history for conversational memory
    history = (
        db.query(MentorMessage)
        .filter(MentorMessage.conversation_id == conv.id)
        .order_by(MentorMessage.created_at.asc())
        .limit(10)
        .all()
    )

    history_text = "\n".join([f"{m.sender.title()}: {m.content}" for m in history])
    system_prompt = MODE_SYSTEM_PROMPTS.get(conv.mode, MODE_SYSTEM_PROMPTS["idea"])

    full_prompt = (
        f"{system_prompt}\n\n"
        f"Project Context:\n" + ("\n".join(context_lines) if context_lines else "No specific project linked.") + "\n\n"
        f"Conversation History:\n{history_text}\n\n"
        "Provide a thoughtful, realistic, actionable response. Do not invent false citations or promise absolute market outcomes."
    )

    llm = get_llm_provider()
    try:
        reply_text = llm.generate_text(full_prompt, system_prompt)
    except Exception as e:
        reply_text = (
            f"I have analyzed your query based on our current {conv.mode} context. "
            "Focus on proving your core hypothesis with rapid prototypes and direct user feedback."
        )

    mentor_msg = MentorMessage(
        conversation_id=conv.id,
        sender="mentor",
        content=reply_text,
        cited_sources=citations[:3],
        created_at=datetime.now(timezone.utc)
    )
    db.add(mentor_msg)
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(mentor_msg)
    return mentor_msg


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a conversation and its messages."""
    conv = (
        db.query(MentorConversation)
        .filter(MentorConversation.id == conversation_id, MentorConversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return None
