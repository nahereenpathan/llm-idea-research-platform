"""initial schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('domain', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'], unique=False)

    # Ideas
    op.create_table(
        'ideas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('problem_statement', sa.Text(), nullable=False),
        sa.Column('proposed_solution', sa.Text(), nullable=False),
        sa.Column('target_audience', sa.String(length=255), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=False),
        sa.Column('intended_use_case', sa.Text(), nullable=False),
        sa.Column('expected_benefits', sa.Text(), nullable=False),
        sa.Column('constraints', sa.Text(), nullable=True),
        sa.Column('estimated_budget', sa.String(length=100), nullable=True),
        sa.Column('technical_preferences', sa.Text(), nullable=True),
        sa.Column('is_selected', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ideas_id'), 'ideas', ['id'], unique=False)
    op.create_index(op.f('ix_ideas_project_id'), 'ideas', ['project_id'], unique=False)

    # Evaluations
    op.create_table(
        'evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('idea_id', sa.Integer(), nullable=False),
        sa.Column('dimension_scores', sa.JSON(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('strengths', sa.JSON(), nullable=False),
        sa.Column('weaknesses', sa.JSON(), nullable=False),
        sa.Column('risks', sa.JSON(), nullable=False),
        sa.Column('evidence_notes', sa.JSON(), nullable=False),
        sa.Column('missing_information', sa.JSON(), nullable=False),
        sa.Column('recommended_experiments', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['idea_id'], ['ideas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluations_id'), 'evaluations', ['id'], unique=False)
    op.create_index(op.f('ix_evaluations_idea_id'), 'evaluations', ['idea_id'], unique=False)
    op.create_index(op.f('ix_evaluations_project_id'), 'evaluations', ['project_id'], unique=False)

    # Comparison results
    op.create_table(
        'comparison_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('configured_weights', sa.JSON(), nullable=False),
        sa.Column('recommended_idea_id', sa.Integer(), nullable=True),
        sa.Column('recommendation_rationale', sa.Text(), nullable=False),
        sa.Column('tradeoff_analysis', sa.JSON(), nullable=False),
        sa.Column('is_tie', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['recommended_idea_id'], ['ideas.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_comparison_results_id'), 'comparison_results', ['id'], unique=False)
    op.create_index(op.f('ix_comparison_results_project_id'), 'comparison_results', ['project_id'], unique=False)

    # Academic papers
    op.create_table(
        'academic_papers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('authors', sa.JSON(), nullable=False),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('publication_date', sa.String(length=50), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('doi', sa.String(length=255), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('citation_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_saved_to_library', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('user_notes', sa.Text(), nullable=True),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_academic_papers_id'), 'academic_papers', ['id'], unique=False)
    op.create_index(op.f('ix_academic_papers_project_id'), 'academic_papers', ['project_id'], unique=False)

    # Patent records
    op.create_table(
        'patent_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('patent_number', sa.String(length=100), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('inventors', sa.JSON(), nullable=False),
        sa.Column('publication_date', sa.String(length=50), nullable=True),
        sa.Column('filing_date', sa.String(length=50), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('is_saved', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('similarity_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patent_records_id'), 'patent_records', ['id'], unique=False)
    op.create_index(op.f('ix_patent_records_project_id'), 'patent_records', ['project_id'], unique=False)

    # Research jobs
    op.create_table(
        'research_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_uuid', sa.String(length=100), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status_message', sa.Text(), nullable=True),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_jobs_id'), 'research_jobs', ['id'], unique=False)
    op.create_index(op.f('ix_research_jobs_job_uuid'), 'research_jobs', ['job_uuid'], unique=True)
    op.create_index(op.f('ix_research_jobs_project_id'), 'research_jobs', ['project_id'], unique=False)

    # Gap analyses
    op.create_table(
        'research_gap_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('idea_id', sa.Integer(), nullable=False),
        sa.Column('existing_approaches', sa.JSON(), nullable=False),
        sa.Column('common_findings', sa.JSON(), nullable=False),
        sa.Column('conflicting_findings', sa.JSON(), nullable=False),
        sa.Column('limitations_in_prior_work', sa.JSON(), nullable=False),
        sa.Column('identified_gaps', sa.JSON(), nullable=False),
        sa.Column('suggested_research_questions', sa.JSON(), nullable=False),
        sa.Column('proposed_evaluation_methods', sa.JSON(), nullable=False),
        sa.Column('citations', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['idea_id'], ['ideas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_research_gap_analyses_id'), 'research_gap_analyses', ['id'], unique=False)
    op.create_index(op.f('ix_research_gap_analyses_project_id'), 'research_gap_analyses', ['project_id'], unique=False)

    # Roadmaps
    op.create_table(
        'implementation_roadmaps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('idea_id', sa.Integer(), nullable=False),
        sa.Column('objectives', sa.JSON(), nullable=False),
        sa.Column('functional_requirements', sa.JSON(), nullable=False),
        sa.Column('nonfunctional_requirements', sa.JSON(), nullable=False),
        sa.Column('mvp_scope', sa.JSON(), nullable=False),
        sa.Column('phased_milestones', sa.JSON(), nullable=False),
        sa.Column('suggested_database_entities', sa.JSON(), nullable=False),
        sa.Column('api_design_endpoints', sa.JSON(), nullable=False),
        sa.Column('recommended_tech_stack', sa.JSON(), nullable=False),
        sa.Column('task_breakdown', sa.JSON(), nullable=False),
        sa.Column('security_considerations', sa.JSON(), nullable=False),
        sa.Column('risks_and_mitigations', sa.JSON(), nullable=False),
        sa.Column('estimated_effort_ranges', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['idea_id'], ['ideas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_implementation_roadmaps_id'), 'implementation_roadmaps', ['id'], unique=False)
    op.create_index(op.f('ix_implementation_roadmaps_project_id'), 'implementation_roadmaps', ['project_id'], unique=False)

    # Mentor conversations & messages
    op.create_table(
        'mentor_conversations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('idea_id', sa.Integer(), nullable=True),
        sa.Column('mode', sa.String(length=50), nullable=False, server_default='idea'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['idea_id'], ['ideas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mentor_conversations_id'), 'mentor_conversations', ['id'], unique=False)
    op.create_index(op.f('ix_mentor_conversations_project_id'), 'mentor_conversations', ['project_id'], unique=False)
    op.create_index(op.f('ix_mentor_conversations_user_id'), 'mentor_conversations', ['user_id'], unique=False)

    op.create_table(
        'mentor_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.Integer(), nullable=False),
        sa.Column('sender', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('cited_sources', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['mentor_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_mentor_messages_id'), 'mentor_messages', ['id'], unique=False)
    op.create_index(op.f('ix_mentor_messages_conversation_id'), 'mentor_messages', ['conversation_id'], unique=False)

    # Reports
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('idea_id', sa.Integer(), nullable=True),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('content_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['idea_id'], ['ideas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)
    op.create_index(op.f('ix_reports_project_id'), 'reports', ['project_id'], unique=False)

    # Presentations & Slides
    op.create_table(
        'presentations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('idea_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('theme', sa.String(length=50), nullable=False, server_default='navy_modern'),
        sa.Column('template_type', sa.String(length=50), nullable=False, server_default='hackathon'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['idea_id'], ['ideas.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_presentations_id'), 'presentations', ['id'], unique=False)
    op.create_index(op.f('ix_presentations_project_id'), 'presentations', ['project_id'], unique=False)

    op.create_table(
        'slides',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('presentation_id', sa.Integer(), nullable=False),
        sa.Column('slide_number', sa.Integer(), nullable=False),
        sa.Column('layout', sa.String(length=50), nullable=False, server_default='bullets'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('subtitle', sa.String(length=255), nullable=True),
        sa.Column('content_json', sa.JSON(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['presentation_id'], ['presentations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slides_id'), 'slides', ['id'], unique=False)
    op.create_index(op.f('ix_slides_presentation_id'), 'slides', ['presentation_id'], unique=False)


def downgrade() -> None:
    op.drop_table('slides')
    op.drop_table('presentations')
    op.drop_table('reports')
    op.drop_table('mentor_messages')
    op.drop_table('mentor_conversations')
    op.drop_table('implementation_roadmaps')
    op.drop_table('research_gap_analyses')
    op.drop_table('research_jobs')
    op.drop_table('patent_records')
    op.drop_table('academic_papers')
    op.drop_table('comparison_results')
    op.drop_table('evaluations')
    op.drop_table('ideas')
    op.drop_table('projects')
    op.drop_table('users')
