"""Initialize database and seed geo-hierarchy data"""
from database import engine, Base, SessionLocal
from models import State, District, Zone, Colony, User, UserRole
from datetime import datetime

def init_database():
    """Create all tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully!")

def seed_geo_hierarchy():
    """Seed geographic hierarchy data: 2 States → 4 Districts each → 8 Zones each → 16 Colonies each"""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_states = db.query(State).count()
        if existing_states > 0:
            print("✓ Geo-hierarchy data already exists!")
            return
        
        print("Seeding geo-hierarchy data...")
        
        # Create 2 states
        states_data = [
            {"name": "Maharashtra", "code": "MH"},
            {"name": "Karnataka", "code": "KA"}
        ]
        
        for state_data in states_data:
            state = State(**state_data)
            db.add(state)
            db.flush()
            
            # Create 4 districts per state
            for dist_num in range(1, 5):
                district = District(
                    name=f"{state.name} District {dist_num}",
                    code=f"{state.code}D{dist_num}",
                    state_id=state.id
                )
                db.add(district)
                db.flush()
                
                # Create 8 zones per district
                for zone_num in range(1, 9):
                    zone = Zone(
                        name=f"{district.name} Zone {zone_num}",
                        code=f"{district.code}Z{zone_num}",
                        district_id=district.id
                    )
                    db.add(zone)
                    db.flush()
                    
                    # Create 16 colonies per zone
                    for colony_num in range(1, 17):
                        colony = Colony(
                            name=f"{zone.name} Colony {colony_num}",
                            code=f"{zone.code}C{colony_num:02d}",
                            zone_id=zone.id
                        )
                        db.add(colony)
        
        db.commit()
        
        # Print statistics
        total_states = db.query(State).count()
        total_districts = db.query(District).count()
        total_zones = db.query(Zone).count()
        total_colonies = db.query(Colony).count()
        
        print(f"""
✓ Geo-hierarchy seeded successfully!
  States: {total_states}
  Districts: {total_districts}
  Zones: {total_zones}
  Colonies: {total_colonies}
        """)
        
    except Exception as e:
        print(f"Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()

def create_super_admin():
    """Create default super admin user"""
    db = SessionLocal()
    
    try:
        # Check if super admin exists
        existing_admin = db.query(User).filter(User.role == UserRole.PLATFORM_OWNER).first()
        if existing_admin:
            print("✓ Super admin already exists!")
            return
        
        print("Creating super admin user...")
        
        # Create super admin (phone: 9999999999)
        admin = User(
            phone="9999999999",
            name="Super Admin",
            email="admin@communityos.com",
            role=UserRole.PLATFORM_OWNER,
            is_active=True,
            is_verified=True,
            reputation_score=1000.0,
            last_login=datetime.utcnow()
        )
        db.add(admin)
        db.commit()
        
        print("✓ Super admin created! Phone: 9999999999")
        
    except Exception as e:
        print(f"Error creating super admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=== Initializing Community OS Database ===\n")
    init_database()
    seed_geo_hierarchy()
    create_super_admin()
    print("\n=== Database initialization complete! ===")
