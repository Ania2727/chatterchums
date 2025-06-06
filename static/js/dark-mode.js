document.addEventListener('DOMContentLoaded', function() {
    // Check for dark mode cookie
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Get theme from cookie
    const themeCookie = getCookie('theme');

    // If no cookie exists yet, check localStorage for backward compatibility
    if (!themeCookie) {
        const savedDarkMode = localStorage.getItem('darkMode');
        if (savedDarkMode === 'enabled') {
            document.body.classList.add('dark-mode');
        }
    }
    // If cookie exists but doesn't match body class, update body class
    else if (themeCookie === 'dark' && !document.body.classList.contains('dark-mode')) {
        document.body.classList.add('dark-mode');
    }
    else if (themeCookie === 'light' && document.body.classList.contains('dark-mode')) {
        document.body.classList.remove('dark-mode');
    }
});