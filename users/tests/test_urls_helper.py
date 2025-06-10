
USERS_URLS = {
    'profile': 'users:profile',
    'delete_profile': 'users:delete_profile', 
    'settings': 'users:settings',
    'logout': 'users:logout',
    'signup': 'users:signup',
    'login': 'users:login',
    'quiz': 'users:quiz',
    'explore': 'users:explore',
    'save_interests': 'users:save_interests',
    'edit_profile': 'users:edit_profile',
    
    'forum_recommendations': '/users/forum-recommendations/',
}

OTHER_URLS = {
    'home': 'home', 
}

def get_url(name):
    if name in USERS_URLS:
        return USERS_URLS[name]
    elif name in OTHER_URLS:
        return OTHER_URLS[name]
    else:
        raise ValueError(f"URL '{name}' not found in URL mapping")