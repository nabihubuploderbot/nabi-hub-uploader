"""
handlers/__init__.py — Handler registration package.

Imports and registers all routers.
"""

from aiogram import Router


def get_handlers_router() -> Router:
    """Create and configure the main handlers router."""
    from handlers.start import router as start_router
    from handlers.upload import router as upload_router
    from handlers.admin_panel import router as admin_panel_router
    from handlers.admin_settings import router as admin_settings_router
    from handlers.admin_broadcast import router as admin_broadcast_router
    from handlers.admin_files import router as admin_files_router
    from handlers.admin_users import router as admin_users_router
    from handlers.admin_channel import router as admin_channel_router
    from handlers.admin_manage import router as admin_manage_router
    from handlers.force_join import router as force_join_router
    from handlers.reaction_lock import router as reaction_lock_router

    main_router = Router(name="main_handlers")

    # Register sub-routers (order matters: more specific first)
    main_router.include_router(start_router)
    main_router.include_router(force_join_router)
    main_router.include_router(reaction_lock_router)
    main_router.include_router(upload_router)
    main_router.include_router(admin_manage_router)      # ← جدید: مدیریت ادمین
    main_router.include_router(admin_channel_router)     # ← جدید: ارسال به کانال/گروه
    main_router.include_router(admin_panel_router)
    main_router.include_router(admin_settings_router)
    main_router.include_router(admin_broadcast_router)
    main_router.include_router(admin_files_router)
    main_router.include_router(admin_users_router)

    return main_router
