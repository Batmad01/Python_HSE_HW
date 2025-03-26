from fastapi import APIRouter
from app.auth.users import auth_backend, fastapi_users
from app.auth.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter()

# Роут авторизации
auth_router = fastapi_users.get_auth_router(auth_backend)
router.include_router(auth_router, prefix="/auth/jwt", tags=["auth"])

# Роут регистрации
register_router = fastapi_users.get_register_router(UserRead, UserCreate)
router.include_router(register_router, prefix="/auth", tags=["auth"])

# Роут сброса пароля
reset_router = fastapi_users.get_reset_password_router()
router.include_router(reset_router, prefix="/auth", tags=["auth"])

# Роут подтверждения e-mail
verify_router = fastapi_users.get_verify_router(UserRead)
router.include_router(verify_router, prefix="/auth", tags=["auth"])

# Роутер профиля – users/me
users_router = fastapi_users.get_users_router(UserRead, UserUpdate)
router.include_router(users_router, prefix="/users", tags=["users"])
