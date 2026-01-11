"""
Community Operating System - Backend API
8-Layer Architecture with PostgreSQL, MongoDB, and Redis
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import logging
from pathlib import Path

# Import database and models
from database import get_db, get_mongo_db, get_redis_client, Base, engine
from models import (
    User, State, District, Zone, Colony, Event, Club, EventParticipation,
    SystemRule, FeatureFlag, ModerationQueue, UserRole, EventStatus, ActivityType
)
from schemas import (
    SendOTPRequest, VerifyOTPRequest, AuthResponse, UserResponse, UserCreate,
    StateResponse, DistrictResponse, ZoneResponse, ColonyResponse,
    EventCreate, EventResponse, ClubCreate, ClubResponse,
    SystemRuleCreate, SystemRuleResponse,
    FeatureFlagCreate, FeatureFlagResponse,
    SystemStatsResponse, LeaderboardResponse, LeaderboardEntry
)
from auth_utils import (
    generate_otp, verify_otp, create_access_token,
    get_current_user, require_role
)

# Create FastAPI app
app = FastAPI(title="Community OS API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ========================
# AUTHENTICATION ENDPOINTS
# ========================

@api_router.post("/auth/send-otp")
async def send_otp(request: SendOTPRequest, db: Session = Depends(get_db)):
    """Send OTP to phone number (Mock: always returns 123456)"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.phone == request.phone).first()
        
        # Generate OTP (mock)
        otp = generate_otp(request.phone)
        
        return {
            "success": True,
            "message": f"OTP sent to {request.phone}",
            "otp": otp,  # Only for development!
            "user_exists": user is not None
        }
    except Exception as e:
        logger.error(f"Error sending OTP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/auth/verify-otp", response_model=AuthResponse)
async def verify_otp_endpoint(request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """Verify OTP and return JWT token"""
    try:
        # Verify OTP
        is_valid = verify_otp(request.phone, request.otp)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired OTP"
            )
        
        # Find or create user
        user = db.query(User).filter(User.phone == request.phone).first()
        
        if not user:
            # Create new user with GENERAL_USER role
            user = User(
                phone=request.phone,
                role=UserRole.GENERAL_USER,
                is_active=True,
                is_verified=False,
                last_login=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
        
        # Create JWT token
        access_token = create_access_token(
            user_id=user.id,
            phone=user.phone,
            role=user.role.value
        )
        
        return AuthResponse(
            access_token=access_token,
            user=UserResponse.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse.from_orm(current_user)


# ========================
# GEOGRAPHY ENDPOINTS
# ========================

@api_router.get("/geo/states", response_model=List[StateResponse])
async def get_states(db: Session = Depends(get_db)):
    """Get all states"""
    states = db.query(State).all()
    return [StateResponse.from_orm(s) for s in states]


@api_router.get("/geo/districts", response_model=List[DistrictResponse])
async def get_districts(state_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get districts, optionally filtered by state"""
    query = db.query(District)
    if state_id:
        query = query.filter(District.state_id == state_id)
    districts = query.all()
    return [DistrictResponse.from_orm(d) for d in districts]


@api_router.get("/geo/zones", response_model=List[ZoneResponse])
async def get_zones(district_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get zones, optionally filtered by district"""
    query = db.query(Zone)
    if district_id:
        query = query.filter(Zone.district_id == district_id)
    zones = query.all()
    return [ZoneResponse.from_orm(z) for z in zones]


@api_router.get("/geo/colonies", response_model=List[ColonyResponse])
async def get_colonies(zone_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Get colonies, optionally filtered by zone"""
    query = db.query(Colony)
    if zone_id:
        query = query.filter(Colony.zone_id == zone_id)
    colonies = query.all()
    return [ColonyResponse.from_orm(c) for c in colonies]


# ========================
# USER PROFILE ENDPOINTS
# ========================

@api_router.put("/users/profile")
async def update_profile(
    name: Optional[str] = None,
    email: Optional[str] = None,
    colony_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    try:
        if name:
            current_user.name = name
        if email:
            current_user.email = email
        if colony_id:
            current_user.colony_id = colony_id
        
        db.commit()
        db.refresh(current_user)
        
        return {"success": True, "user": UserResponse.from_orm(current_user)}
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# PLATFORM OWNER ENDPOINTS (Layer 1)
# ========================

@api_router.get("/admin/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: User = Depends(require_role([UserRole.PLATFORM_OWNER, UserRole.PLATFORM_OPERATIONS])),
    db: Session = Depends(get_db)
):
    """Get system-wide statistics"""
    try:
        total_users = db.query(User).count()
        
        # Active users today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        active_users_today = db.query(User).filter(User.last_login >= today).count()
        
        total_events = db.query(Event).count()
        ongoing_events = db.query(Event).filter(Event.status == EventStatus.ONGOING).count()
        total_clubs = db.query(Club).count()
        total_colonies = db.query(Colony).count()
        pending_moderations = db.query(ModerationQueue).filter(ModerationQueue.status == "pending").count()
        
        return SystemStatsResponse(
            total_users=total_users,
            active_users_today=active_users_today,
            total_events=total_events,
            ongoing_events=ongoing_events,
            total_clubs=total_clubs,
            total_colonies=total_colonies,
            pending_moderations=pending_moderations
        )
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/admin/system-rules", response_model=List[SystemRuleResponse])
async def get_system_rules(
    current_user: User = Depends(require_role([UserRole.PLATFORM_OWNER])),
    db: Session = Depends(get_db)
):
    """Get all system rules"""
    rules = db.query(SystemRule).all()
    return [SystemRuleResponse.from_orm(r) for r in rules]


@api_router.post("/admin/system-rules", response_model=SystemRuleResponse)
async def create_system_rule(
    rule: SystemRuleCreate,
    current_user: User = Depends(require_role([UserRole.PLATFORM_OWNER])),
    db: Session = Depends(get_db)
):
    """Create or update a system rule"""
    try:
        # Check if rule exists
        existing_rule = db.query(SystemRule).filter(SystemRule.rule_key == rule.rule_key).first()
        
        if existing_rule:
            # Update existing rule
            existing_rule.rule_value = rule.rule_value
            existing_rule.description = rule.description
            existing_rule.updated_by_id = current_user.id
            existing_rule.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_rule)
            return SystemRuleResponse.from_orm(existing_rule)
        else:
            # Create new rule
            new_rule = SystemRule(
                rule_key=rule.rule_key,
                rule_value=rule.rule_value,
                description=rule.description,
                updated_by_id=current_user.id
            )
            db.add(new_rule)
            db.commit()
            db.refresh(new_rule)
            return SystemRuleResponse.from_orm(new_rule)
            
    except Exception as e:
        logger.error(f"Error creating system rule: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/admin/feature-flags", response_model=List[FeatureFlagResponse])
async def get_feature_flags(
    current_user: User = Depends(require_role([UserRole.PLATFORM_OWNER])),
    db: Session = Depends(get_db)
):
    """Get all feature flags"""
    flags = db.query(FeatureFlag).all()
    return [FeatureFlagResponse.from_orm(f) for f in flags]


@api_router.post("/admin/feature-flags", response_model=FeatureFlagResponse)
async def create_feature_flag(
    flag: FeatureFlagCreate,
    current_user: User = Depends(require_role([UserRole.PLATFORM_OWNER])),
    db: Session = Depends(get_db)
):
    """Create or update a feature flag"""
    try:
        existing_flag = db.query(FeatureFlag).filter(FeatureFlag.feature_name == flag.feature_name).first()
        
        if existing_flag:
            existing_flag.is_enabled = flag.is_enabled
            existing_flag.rollout_percentage = flag.rollout_percentage
            existing_flag.enabled_districts = flag.enabled_districts
            existing_flag.description = flag.description
            existing_flag.updated_by_id = current_user.id
            existing_flag.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(existing_flag)
            return FeatureFlagResponse.from_orm(existing_flag)
        else:
            new_flag = FeatureFlag(
                feature_name=flag.feature_name,
                is_enabled=flag.is_enabled,
                rollout_percentage=flag.rollout_percentage,
                enabled_districts=flag.enabled_districts,
                description=flag.description,
                updated_by_id=current_user.id
            )
            db.add(new_flag)
            db.commit()
            db.refresh(new_flag)
            return FeatureFlagResponse.from_orm(new_flag)
            
    except Exception as e:
        logger.error(f"Error creating feature flag: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# EVENT ENDPOINTS
# ========================

@api_router.post("/events", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new event"""
    try:
        new_event = Event(
            title=event.title,
            description=event.description,
            activity_type=event.activity_type,
            start_time=event.start_time,
            end_time=event.end_time,
            colony_id=event.colony_id,
            location_details=event.location_details,
            creator_id=current_user.id,
            club_id=event.club_id,
            max_participants=event.max_participants,
            is_paid=event.is_paid,
            entry_fee=event.entry_fee,
            status=EventStatus.APPROVED if current_user.role in [UserRole.PLATFORM_OWNER, UserRole.CITY_ADMIN] else EventStatus.PENDING
        )
        db.add(new_event)
        db.commit()
        db.refresh(new_event)
        
        return EventResponse.from_orm(new_event)
    except Exception as e:
        logger.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/events", response_model=List[EventResponse])
async def get_events(
    colony_id: Optional[int] = None,
    status: Optional[EventStatus] = None,
    activity_type: Optional[ActivityType] = None,
    db: Session = Depends(get_db)
):
    """Get events with optional filters"""
    query = db.query(Event)
    
    if colony_id:
        query = query.filter(Event.colony_id == colony_id)
    if status:
        query = query.filter(Event.status == status)
    if activity_type:
        query = query.filter(Event.activity_type == activity_type)
    
    events = query.order_by(desc(Event.start_time)).limit(100).all()
    return [EventResponse.from_orm(e) for e in events]


@api_router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get event by ID"""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventResponse.from_orm(event)


# ========================
# LEADERBOARD ENDPOINTS
# ========================

@api_router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    scope: str = "national",  # national, state, district, zone, colony
    geo_id: Optional[int] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get leaderboard by scope"""
    try:
        query = db.query(User).filter(User.is_active == True)
        
        # Filter by geography
        if scope == "colony" and geo_id:
            query = query.filter(User.colony_id == geo_id)
        elif scope == "zone" and geo_id:
            zone_colonies = db.query(Colony.id).filter(Colony.zone_id == geo_id).subquery()
            query = query.filter(User.colony_id.in_(zone_colonies))
        elif scope == "district" and geo_id:
            district_colonies = db.query(Colony.id).join(Zone).filter(Zone.district_id == geo_id).subquery()
            query = query.filter(User.colony_id.in_(district_colonies))
        elif scope == "state" and geo_id:
            state_colonies = db.query(Colony.id).join(Zone).join(District).filter(District.state_id == geo_id).subquery()
            query = query.filter(User.colony_id.in_(state_colonies))
        
        # Order by reputation and limit
        users = query.order_by(desc(User.reputation_score)).limit(limit).all()
        
        # Build leaderboard entries
        entries = []
        for rank, user in enumerate(users, 1):
            entries.append(LeaderboardEntry(
                user_id=user.id,
                name=user.name or f"User {user.id}",
                reputation_score=user.reputation_score,
                current_streak=user.current_streak,
                total_activities=user.total_activities,
                rank=rank
            ))
        
        return LeaderboardResponse(scope=scope, entries=entries)
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# CLUB ENDPOINTS
# ========================

@api_router.post("/clubs", response_model=ClubResponse)
async def create_club(
    club: ClubCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new club"""
    try:
        new_club = Club(
            name=club.name,
            description=club.description,
            club_type=club.club_type,
            owner_id=current_user.id,
            colony_id=club.colony_id,
            district_id=club.district_id,
            is_verified=False
        )
        db.add(new_club)
        db.commit()
        db.refresh(new_club)
        
        return ClubResponse.from_orm(new_club)
    except Exception as e:
        logger.error(f"Error creating club: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/clubs", response_model=List[ClubResponse])
async def get_clubs(
    colony_id: Optional[int] = None,
    district_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get clubs with optional filters"""
    query = db.query(Club)
    
    if colony_id:
        query = query.filter(Club.colony_id == colony_id)
    if district_id:
        query = query.filter(Club.district_id == district_id)
    
    clubs = query.limit(100).all()
    return [ClubResponse.from_orm(c) for c in clubs]


# ========================
# ROOT ENDPOINT
# ========================

@api_router.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Community OS API v1.0.0",
        "status": "operational",
        "architecture": "8-Layer Hierarchy",
        "databases": ["PostgreSQL", "MongoDB", "Redis"]
    }


# ========================
# HEALTH CHECK
# ========================

@api_router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test PostgreSQL
        db.execute("SELECT 1")
        
        # Test Redis
        redis_client = get_redis_client()
        redis_client.ping()
        
        # Test MongoDB
        mongo_db = get_mongo_db()
        await mongo_db.command("ping")
        
        return {
            "status": "healthy",
            "postgresql": "connected",
            "redis": "connected",
            "mongodb": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Include router
app.include_router(api_router)


# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Community OS API Starting...")
    logger.info("8-Layer Architecture: Platform Owner → Operations → Authority → City Admin → Club → Leader → Verified User → General User")
    logger.info("Databases: PostgreSQL (users, geo, events) + MongoDB (logs, proofs) + Redis (cache, OTP)")
    logger.info("=" * 60)


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Community OS API Shutting down...")
