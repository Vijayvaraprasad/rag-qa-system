import time
from functools import wraps

REQUESTS = {}
LIMIT = 10
WINDOW = 60

def allow(ip):
    now = time.time()
    REQUESTS.setdefault(ip, [])
    REQUESTS[ip] = [t for t in REQUESTS[ip] if now - t < WINDOW]

    if len(REQUESTS[ip]) >= LIMIT:
        return False

    REQUESTS[ip].append(now)
    return True


def rate_limit(max_calls=10, time_window=60):
    """
    Decorator for rate limiting function calls.
    
    Args:
        max_calls: Maximum number of calls allowed
        time_window: Time window in seconds
    """
    def decorator(func):
        call_times = []
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal call_times
            now = time.time()
            
            # Remove calls outside the time window
            call_times = [t for t in call_times if now - t < time_window]
            
            # Check if rate limit exceeded
            if len(call_times) >= max_calls:
                raise RuntimeError(f"Rate limit exceeded: {max_calls} calls per {time_window}s")
            
            # Record this call
            call_times.append(now)
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
