import enum

class RoleEnum(enum.Enum): # System-level roles
    SYSTEM_ADMIN = "system_admin"  # Platform owner
    USER = "user"              # Regular user of the platform, default

class CompanyRoleEnum(enum.Enum): # Roles within a company
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"
    # OWNER is an implicit role, typically checked via company.owner_id