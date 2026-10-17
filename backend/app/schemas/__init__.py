from app.schemas.auth import UserRegister, UserLogin, TokenResponse, TokenData
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut
from app.schemas.idea import IdeaCreate, IdeaUpdate, IdeaOut
from app.schemas.evaluation import (
    DimensionScores, DimensionWeights, EvaluationOut,
    ComparisonRequest, ComparisonResultOut, FullProjectEvaluationResponse
)
from app.schemas.paper import (
    AcademicPaperCreate, AcademicPaperUpdate, AcademicPaperOut, PaperSearchRequest
)
from app.schemas.patent import (
    PatentRecordCreate, PatentRecordUpdate, PatentRecordOut, PatentSearchRequest
)
from app.schemas.research_job import ResearchJobOut
from app.schemas.gap_analysis import ResearchGapAnalysisOut, GapAnalysisGenerateRequest
from app.schemas.roadmap import (
    ImplementationRoadmapOut, RoadmapGenerateRequest, TaskStatusUpdateRequest
)
from app.schemas.mentor import (
    MentorConversationCreate, MentorConversationOut, MentorMessageOut, SendMessageRequest
)
from app.schemas.report import ReportCreate, ReportUpdate, ReportOut
from app.schemas.presentation import (
    PresentationCreate, PresentationUpdate, PresentationOut,
    SlideCreate, SlideUpdate, SlideOut
)

__all__ = [
    "UserRegister", "UserLogin", "TokenResponse", "TokenData",
    "UserCreate", "UserUpdate", "UserOut",
    "ProjectCreate", "ProjectUpdate", "ProjectOut",
    "IdeaCreate", "IdeaUpdate", "IdeaOut",
    "DimensionScores", "DimensionWeights", "EvaluationOut",
    "ComparisonRequest", "ComparisonResultOut", "FullProjectEvaluationResponse",
    "AcademicPaperCreate", "AcademicPaperUpdate", "AcademicPaperOut", "PaperSearchRequest",
    "PatentRecordCreate", "PatentRecordUpdate", "PatentRecordOut", "PatentSearchRequest",
    "ResearchJobOut",
    "ResearchGapAnalysisOut", "GapAnalysisGenerateRequest",
    "ImplementationRoadmapOut", "RoadmapGenerateRequest", "TaskStatusUpdateRequest",
    "MentorConversationCreate", "MentorConversationOut", "MentorMessageOut", "SendMessageRequest",
    "ReportCreate", "ReportUpdate", "ReportOut",
    "PresentationCreate", "PresentationUpdate", "PresentationOut",
    "SlideCreate", "SlideUpdate", "SlideOut",
]
