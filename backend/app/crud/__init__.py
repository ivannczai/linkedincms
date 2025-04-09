"""
CRUD operations package.

This package contains CRUD (Create, Read, Update, Delete) operations for models.
"""
from app.crud import user, client, strategy, content, scheduled_post # Add scheduled_post

# Re-export user CRUD operations for backward compatibility
from app.crud.user import (
    get as get_user,
    get_by_email,
    create as create_user,
    update as update_user,
    authenticate,
    is_active,
    is_admin,
    update_linkedin_details, # Add linkedin update function
)

# Re-export client CRUD operations
from app.crud.client import (
    get as get_client,
    get_by_user_id,
    get_multi as get_clients,
    create as create_client,
    update as update_client,
    delete as delete_client,
)

# Re-export strategy CRUD operations
from app.crud.strategy import (
    get as get_strategy,
    get_by_client_id,
    get_multi as get_strategies,
    create as create_strategy,
    update as update_strategy,
    delete as delete_strategy,
)

# Re-export content CRUD operations
from app.crud.content import (
    get as get_content,
    get_multi as get_contents,
    create as create_content,
    update as update_content,
    delete as delete_content,
    update_status as update_content_status,
    mark_as_posted,
    rate_content, # Add rate_content
)

# Re-export scheduled_post CRUD operations (optional, but good practice)
from app.crud.scheduled_post import (
    create_scheduled_post,
    get_scheduled_post,
    get_scheduled_posts_by_user,
    get_pending_posts_to_publish,
    update_post_status,
    delete_scheduled_post,
)


__all__ = [
    "user",
    "client",
    "strategy",
    "content",
    "scheduled_post", # Add scheduled_post
    "get_user",
    "get_by_email",
    "create_user",
    "update_user",
    "authenticate",
    "is_active",
    "is_admin",
    "update_linkedin_details", # Add linkedin update function
    "get_client",
    "get_by_user_id",
    "get_clients",
    "create_client",
    "update_client",
    "delete_client",
    "get_strategy",
    "get_by_client_id",
    "get_strategies",
    "create_strategy",
    "update_strategy",
    "delete_strategy",
    "get_content",
    "get_contents",
    "create_content",
    "update_content",
    "delete_content",
    "update_content_status",
    "mark_as_posted",
    "rate_content", # Add rate_content to __all__
    "create_scheduled_post", # Add scheduled post functions
    "get_scheduled_post",
    "get_scheduled_posts_by_user",
    "get_pending_posts_to_publish",
    "update_post_status",
    "delete_scheduled_post",
]
