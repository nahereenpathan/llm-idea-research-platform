import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.idea import Idea
from app.models.paper import AcademicPaper
from app.models.patent import PatentRecord
from app.models.mentor import MentorConversation, MentorMessage
from app.schemas.mentor import (
    MentorConversationCreate,
    MentorConversationUpdate,
    MentorConversationOut,
    MentorMessageOut,
    SendMessageRequest
)
from app.api.v1.deps import get_current_user
from app.services.ai.factory import get_llm_provider

logger = logging.getLogger(__name__)
router = APIRouter()

MODE_SYSTEM_PROMPTS = {
    "idea": (
        "You are the Idea Mentor for IdeaLens. Help innovators sharpen problem significance, "
        "clarify target user personas, articulate unique value propositions, and identify blind spots."
    ),
    "research": (
        "You are the Research Mentor for IdeaLens. Help formulate academic hypotheses, "
        "ground concepts in peer-reviewed literature and patent precedents, and evaluate empirical evidence quality."
    ),
    "technical": (
        "You are the Technical Mentor for IdeaLens. Advise on clean architecture, scalable data models, "
        "RESTful API design, latency optimization, security boundaries, and infrastructure feasibility."
    ),
    "product": (
        "You are the Product Mentor for IdeaLens. Guide ruthless MVP scoping, prioritize user stories, "
        "design frictionless user journeys, and eliminate feature bloat."
    ),
    "business": (
        "You are the Business Mentor for IdeaLens. Analyze monetization strategies, pricing tiers, "
        "unit economics, competitive defensibility, distribution channels, and go-to-market barriers."
    ),
    "validation": (
        "You are the Validation Mentor for IdeaLens. Design rigorous customer discovery interviews, "
        "smoke tests, landing page experiments, and quantitative validation metrics."
    ),
    "pitch": (
        "You are the Pitch Mentor for IdeaLens. Refine executive storytelling, polish elevator pitches, "
        "critique presentation decks, and prepare founders for technical and investor diligence questions."
    )
}


def build_mentor_context(conv: MentorConversation, db: Session) -> str:
    """Builds project and idea context for prompt injection without leaking cross-tenant data."""
    context_lines = []
    if conv.project_id:
        proj = db.query(Project).filter(Project.id == conv.project_id).first()
        if proj:
            context_lines.append(f"Project Title: {proj.title}")
            if proj.domain:
                context_lines.append(f"Domain/Industry: {proj.domain}")
            if proj.description:
                context_lines.append(f"Project Description: {proj.description}")

        # Linked or selected idea
        idea = None
        if conv.idea_id:
            idea = db.query(Idea).filter(Idea.id == conv.idea_id).first()
        else:
            idea = db.query(Idea).filter(Idea.project_id == conv.project_id, Idea.is_selected == True).first()
            if not idea:
                idea = db.query(Idea).filter(Idea.project_id == conv.project_id).first()

        if idea:
            context_lines.append(f"Selected Idea: {idea.title}")
            context_lines.append(f"Problem Statement: {idea.problem_statement}")
            context_lines.append(f"Proposed Solution: {idea.proposed_solution}")
            if idea.target_audience:
                context_lines.append(f"Target Audience: {idea.target_audience}")

        # Saved papers
        papers = db.query(AcademicPaper).filter(AcademicPaper.project_id == conv.project_id).limit(3).all()
        if papers:
            context_lines.append("Saved Research Papers:")
            for p in papers:
                context_lines.append(f"- {p.title} ({p.publication_year or 'Recent'})")

        # Saved patents
        patents = db.query(PatentRecord).filter(PatentRecord.project_id == conv.project_id).limit(2).all()
        if patents:
            context_lines.append("Saved Patents:")
            for pat in patents:
                context_lines.append(f"- {pat.patent_number}: {pat.title}")

    return "\n".join(context_lines) if context_lines else "No specific project linked."


@router.get("/conversations", response_model=List[MentorConversationOut])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all persistent AI mentor conversations for the authenticated user."""
    return (
        db.query(MentorConversation)
        .filter(MentorConversation.user_id == current_user.id)
        .order_by(MentorConversation.updated_at.desc())
        .all()
    )


@router.post("/conversations", response_model=MentorConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(
    conv_in: MentorConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new mentor session with selected discipline and optional project context."""
    if conv_in.project_id:
        proj = db.query(Project).filter(
            Project.id == conv_in.project_id,
            Project.user_id == current_user.id
        ).first()
        if not proj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or unauthorized")

    mode_key = conv_in.mode.lower() if conv_in.mode.lower() in MODE_SYSTEM_PROMPTS else "idea"
    title = conv_in.title or f"{mode_key.title()} Mentoring Session"

    conv = MentorConversation(
        user_id=current_user.id,
        project_id=conv_in.project_id,
        idea_id=conv_in.idea_id,
        mode=mode_key,
        title=title,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)

    # Initial mentor greeting
    greeting = (
        f"Welcome! I am your {mode_key.title()} Mentor. "
        "How can I assist you in testing hypotheses, refining architecture, or stress-testing your concept today?"
    )
    initial_msg = MentorMessage(
        conversation_id=conv.id,
        sender="mentor",
        content=greeting,
        cited_sources=[],
        created_at=datetime.now(timezone.utc)
    )
    db.add(initial_msg)
    db.commit()
    db.refresh(conv)
    return conv


@router.get("/conversations/{conversation_id}", response_model=MentorConversationOut)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns a conversation and its complete chronological message history."""
    conv = (
        db.query(MentorConversation)
        .filter(MentorConversation.id == conversation_id, MentorConversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.put("/conversations/{conversation_id}", response_model=MentorConversationOut)
def update_conversation(
    conversation_id: int,
    conv_update: MentorConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allows renaming a conversation title or switching mode / linked idea."""
    conv = (
        db.query(MentorConversation)
        .filter(MentorConversation.id == conversation_id, MentorConversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    if conv_update.title is not None:
        conv.title = conv_update.title.strip() or conv.title
    if conv_update.mode is not None:
        if conv_update.mode.lower() in MODE_SYSTEM_PROMPTS:
            conv.mode = conv_update.mode.lower()
    if conv_update.idea_id is not None:
        conv.idea_id = conv_update.idea_id
    if conv_update.project_id is not None:
        # Verify ownership
        proj = db.query(Project).filter(
            Project.id == conv_update.project_id,
            Project.user_id == current_user.id
        ).first()
        if not proj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or unauthorized")
        conv.project_id = conv_update.project_id

    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conv)
    return conv


@router.post("/conversations/{conversation_id}/messages", response_model=MentorMessageOut)
def send_message(
    conversation_id: int,
    msg_in: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Appends a user message, injects project context and conversation history,
    generates mentor guidance, and persists the response.
    """
    conv = (
        db.query(MentorConversation)
        .filter(MentorConversation.id == conversation_id, MentorConversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    user_msg = MentorMessage(
        conversation_id=conv.id,
        sender="user",
        content=msg_in.content.strip(),
        cited_sources=[],
        created_at=datetime.now(timezone.utc)
    )
    db.add(user_msg)
    db.commit()

    # Build context and citations
    context_str = build_mentor_context(conv, db)

    # Relevant project citations
    citations = []
    if conv.project_id:
        papers = db.query(AcademicPaper).filter(AcademicPaper.project_id == conv.project_id).limit(3).all()
        for p in papers:
            citations.append({
                "source_type": "paper",
                "title": p.title,
                "url": p.source_url or (f"https://doi.org/{p.doi}" if p.doi else "")
            })

    # History
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
        f"Project Context:\n{context_str}\n\n"
        f"Recent Conversation History:\n{history_text}\n\n"
        "Provide an actionable, structured, realistic mentor response. "
        "Highlight practical next steps and open risks. Never fabricate false claims or guarantee market success."
    )

    llm = get_llm_provider()
    try:
        reply_text = llm.generate_text(full_prompt, system_prompt)
    except Exception as e:
        logger.error(f"Error generating mentor response: {e}")
        reply_text = (
            f"As your {conv.mode.title()} Mentor, I recommend de-risking this step through rapid iteration: "
            "1. Confirm user pain with 5 targeted interviews. "
            "2. Build an isolated proof-of-concept before expanding system scope. "
            "3. Track concrete leading indicators rather than vanity metrics."
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


@router.post("/conversations/{conversation_id}/messages/stream")
def send_message_stream(
    conversation_id: int,
    msg_in: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Streams mentor response tokens via Server-Sent Events (SSE).
    Persists the final generated mentor message into PostgreSQL.
    """
    conv = (
        db.query(MentorConversation)
        .filter(MentorConversation.id == conversation_id, MentorConversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    user_msg = MentorMessage(
        conversation_id=conv.id,
        sender="user",
        content=msg_in.content.strip(),
        cited_sources=[],
        created_at=datetime.now(timezone.utc)
    )
    db.add(user_msg)
    db.commit()

    context_str = build_mentor_context(conv, db)
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
        f"Project Context:\n{context_str}\n\n"
        f"Recent Conversation History:\n{history_text}\n\n"
        "Provide an actionable, structured, realistic mentor response."
    )

    llm = get_llm_provider()
    try:
        reply_text = llm.generate_text(full_prompt, system_prompt)
    except Exception as e:
        logger.error(f"Error in mentor streaming generation: {e}")
        reply_text = (
            f"Here are key recommendations for your {conv.mode} focus: "
            "1. Conduct structured discovery interviews. "
            "2. Validate core architectural assumptions early. "
            "3. Establish measurable validation criteria."
        )

    # Persist mentor message
    mentor_msg = MentorMessage(
        conversation_id=conv.id,
        sender="mentor",
        content=reply_text,
        cited_sources=[],
        created_at=datetime.now(timezone.utc)
    )
    db.add(mentor_msg)
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(mentor_msg)

    async def event_generator():
        # Stream response in natural word-chunks
        words = reply_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            payload = json.dumps({"chunk": chunk, "done": False})
            yield f"data: {payload}\n\n"

        # Final message payload
        final_payload = json.dumps({
            "chunk": "",
            "done": True,
            "message": {
                "id": mentor_msg.id,
                "conversation_id": mentor_msg.conversation_id,
                "sender": mentor_msg.sender,
                "content": mentor_msg.content,
                "cited_sources": mentor_msg.cited_sources,
                "created_at": mentor_msg.created_at.isoformat()
            }
        })
        yield f"data: {final_payload}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
