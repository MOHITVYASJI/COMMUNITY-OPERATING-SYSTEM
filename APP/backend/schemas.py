"""Pydantic schemas for API request/response models"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from models import UserRole, ActivityType, EventStatus

# Auth Schemas
class SendOTPRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)

class VerifyOTPRequest(BaseModel):
    phone: str
    otp: str

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

# User Schemas
class UserBase(BaseModel):
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None

class UserCreate(UserBase):
    colony_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    phone: str
    name: Optional[str]
    email: Optional[str]
    role: UserRole
    colony_id: Optional[int]
    reputation_score: float
    current_streak: int
    longest_streak: int
    total_activities: int
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Geo Schemas
class ColonyResponse(BaseModel):
    id: int
    name: str
    code: str
    zone_id: int
    
    class Config:
        from_attributes = True

class ZoneResponse(BaseModel):
    id: int
    name: str
    code: str
    district_id: int
    colonies: List[ColonyResponse] = []
    
    class Config:
        from_attributes = True

class DistrictResponse(BaseModel):
    id: int
    name: str
    code: str
    state_id: int
    
    class Config:
        from_attributes = True

class StateResponse(BaseModel):
    id: int
    name: str
    code: str
    
    class Config:
        from_attributes = True

# Event Schemas
class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    activity_type: ActivityType
    start_time: datetime
    end_time: datetime
    colony_id: int
    location_details: Optional[str] = None
    max_participants: Optional[int] = None
    is_paid: bool = False
    entry_fee: float = 0.0
    club_id: Optional[int] = None

class EventResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    activity_type: ActivityType
    start_time: datetime
    end_time: datetime
    colony_id: int
    location_details: Optional[str]
    creator_id: int
    club_id: Optional[int]
    max_participants: Optional[int]
    current_participants: int
    status: EventStatus
    is_paid: bool
    entry_fee: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Club Schemas
class ClubCreate(BaseModel):
    name: str
    description: Optional[str] = None
    club_type: str
    colony_id: Optional[int] = None
    district_id: Optional[int] = None

class ClubResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    club_type: str
    owner_id: int
    colony_id: Optional[int]
    district_id: Optional[int]
    is_verified: bool
    subscription_tier: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# System Rules Schemas
class SystemRuleCreate(BaseModel):
    rule_key: str
    rule_value: str
    description: Optional[str] = None

class SystemRuleResponse(BaseModel):
    id: int
    rule_key: str
    rule_value: str
    description: Optional[str]
    updated_by_id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Feature Flag Schemas
class FeatureFlagCreate(BaseModel):
    feature_name: str
    is_enabled: bool = False
    rollout_percentage: float = 0.0
    enabled_districts: Optional[List[int]] = None
    description: Optional[str] = None

class FeatureFlagResponse(BaseModel):
    id: int
    feature_name: str
    is_enabled: bool
    rollout_percentage: float
    enabled_districts: Optional[List[int]]
    description: Optional[str]
    updated_by_id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Analytics Schemas
class SystemStatsResponse(BaseModel):
    total_users: int
    active_users_today: int
    total_events: int
    ongoing_events: int
    total_clubs: int
    total_colonies: int
    pending_moderations: int

class LeaderboardEntry(BaseModel):
    user_id: int
    name: str
    reputation_score: float
    current_streak: int
    total_activities: int
    rank: int

class LeaderboardResponse(BaseModel):
    scope: str  # colony, zone, district, state, national
    entries: List[LeaderboardEntry]
