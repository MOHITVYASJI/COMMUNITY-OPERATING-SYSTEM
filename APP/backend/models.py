"""PostgreSQL Database Models - 8 Layer Architecture"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Float, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

# Enums for User Roles (8 Layers)
class UserRole(str, enum.Enum):
    PLATFORM_OWNER = "platform_owner"  # Layer 1
    PLATFORM_OPERATIONS = "platform_operations"  # Layer 2
    POLICY_AUTHORITY = "policy_authority"  # Layer 3
    CITY_ADMIN = "city_admin"  # Layer 4
    CLUB_ORGANIZER = "club_organizer"  # Layer 5
    COMMUNITY_LEADER = "community_leader"  # Layer 6
    VERIFIED_USER = "verified_user"  # Layer 7
    GENERAL_USER = "general_user"  # Layer 8

class ActivityType(str, enum.Enum):
    SPORTS = "sports"
    WALKING = "walking"
    RUNNING = "running"
    CYCLING = "cycling"
    YOGA = "yoga"
    GYM = "gym"
    SWIMMING = "swimming"
    STUDY = "study"
    SOCIAL = "social"
    VOLUNTEERING = "volunteering"
    OTHER = "other"

class EventStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# Geo-Hierarchy Models
class State(Base):
    __tablename__ = "states"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(10), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    districts = relationship("District", back_populates="state", cascade="all, delete-orphan")

class District(Base):
    __tablename__ = "districts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    state = relationship("State", back_populates="districts")
    zones = relationship("Zone", back_populates="district", cascade="all, delete-orphan")

class Zone(Base):
    __tablename__ = "zones"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    district = relationship("District", back_populates="zones")
    colonies = relationship("Colony", back_populates="zone", cascade="all, delete-orphan")

class Colony(Base):
    __tablename__ = "colonies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    zone = relationship("Zone", back_populates="colonies")
    users = relationship("User", back_populates="colony")
    events = relationship("Event", back_populates="colony")

# User Model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.GENERAL_USER, nullable=False)
    
    # Geographic assignment
    colony_id = Column(Integer, ForeignKey("colonies.id"), nullable=True)
    assigned_district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)  # For city admins
    
    # Gamification
    reputation_score = Column(Float, default=0.0)
    current_streak = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    total_activities = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    colony = relationship("Colony", back_populates="users")
    assigned_district = relationship("District", foreign_keys=[assigned_district_id])
    created_events = relationship("Event", back_populates="creator", foreign_keys="Event.creator_id")
    participations = relationship("EventParticipation", back_populates="user", foreign_keys="EventParticipation.user_id")

# Club/Association Model
class Club(Base):
    __tablename__ = "clubs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    club_type = Column(String(50), nullable=False)  # sports, education, social, etc.
    
    # Owner
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Geographic location
    colony_id = Column(Integer, ForeignKey("colonies.id"), nullable=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=True)
    
    # Status
    is_verified = Column(Boolean, default=False)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # City admin who verified
    
    # Monetization hooks
    subscription_tier = Column(String(20), default="free")  # free, basic, premium
    commission_percentage = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    events = relationship("Event", back_populates="club")

# Event Model
class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    activity_type = Column(Enum(ActivityType), nullable=False)
    
    # Time and location
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    colony_id = Column(Integer, ForeignKey("colonies.id"), nullable=False)
    location_details = Column(Text, nullable=True)
    
    # Creator (can be club or individual)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    club_id = Column(Integer, ForeignKey("clubs.id"), nullable=True)
    
    # Capacity
    max_participants = Column(Integer, nullable=True)
    current_participants = Column(Integer, default=0)
    
    # Status and approval
    status = Column(Enum(EventStatus), default=EventStatus.PENDING)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Monetization
    is_paid = Column(Boolean, default=False)
    entry_fee = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    colony = relationship("Colony", back_populates="events")
    creator = relationship("User", back_populates="created_events", foreign_keys=[creator_id])
    club = relationship("Club", back_populates="events")
    approved_by = relationship("User", foreign_keys=[approved_by_id])
    participations = relationship("EventParticipation", back_populates="event")

# Event Participation
class EventParticipation(Base):
    __tablename__ = "event_participations"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Participation status
    joined_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=False)
    proof_submitted = Column(Boolean, default=False)
    proof_verified = Column(Boolean, default=False)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="participations")
    user = relationship("User", back_populates="participations", foreign_keys=[user_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])

# System Rules (Platform Owner Control)
class SystemRule(Base):
    __tablename__ = "system_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_key = Column(String(100), unique=True, nullable=False)
    rule_value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    updated_by = relationship("User", foreign_keys=[updated_by_id])

# Feature Flags (Platform Owner Control)
class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    
    id = Column(Integer, primary_key=True, index=True)
    feature_name = Column(String(100), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=False)
    rollout_percentage = Column(Float, default=0.0)  # For gradual rollout
    enabled_districts = Column(JSON, nullable=True)  # List of district IDs where enabled
    description = Column(Text, nullable=True)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    updated_by = relationship("User", foreign_keys=[updated_by_id])

# Moderation Queue (Platform Operations)
class ModerationQueue(Base):
    __tablename__ = "moderation_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String(50), nullable=False)  # event, proof, user, club
    content_id = Column(Integer, nullable=False)
    reported_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reason = Column(Text, nullable=False)
    
    status = Column(String(20), default="pending")  # pending, resolved, dismissed
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolution_note = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    reported_by = relationship("User", foreign_keys=[reported_by_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
