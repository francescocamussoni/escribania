# Security Audit Guide

## Purpose
Baseline security checks for all generated code. These are minimum requirements that complement developer's custom security standards.

> **Note:** Examples below use Python syntax. Apply the same patterns using your project's language (TypeScript, Java, Go, Ruby, etc.). The principles are universal — only the syntax changes.

---

## Security Checklist

### Authentication & Authorization
- [ ] Authentication checks present on protected endpoints
- [ ] Authorization checks verify user permissions
- [ ] No authentication logic in client-side code
- [ ] Session tokens are secure (httpOnly, secure, sameSite)
- [ ] Passwords are hashed (bcrypt, argon2, scrypt)
- [ ] No passwords in logs or error messages

### Input Validation
- [ ] All user input is validated before processing
- [ ] Whitelist validation preferred over blacklist
- [ ] Type checking on all inputs
- [ ] Length limits on string inputs
- [ ] Range validation on numeric inputs
- [ ] File upload validation (type, size, content)

### SQL Injection Prevention
- [ ] Use parameterized queries or ORM
- [ ] NEVER concatenate SQL with user input
- [ ] Validate data types before queries
- [ ] Use least privilege DB accounts

### XSS (Cross-Site Scripting) Prevention
- [ ] Escape all user-generated content in HTML
- [ ] Use Content Security Policy headers
- [ ] Sanitize HTML if user HTML is allowed
- [ ] No `eval()` or `innerHTML` with user data
- [ ] Use framework's built-in escaping

### CSRF (Cross-Site Request Forgery) Prevention
- [ ] CSRF tokens on state-changing operations
- [ ] SameSite cookie attribute set
- [ ] Verify Origin/Referer headers
- [ ] Use POST/PUT/DELETE for state changes (not GET)

### Secrets Management
- [ ] No hardcoded credentials, API keys, or tokens
- [ ] Secrets loaded from environment variables
- [ ] No secrets in logs or error messages
- [ ] No secrets in client-side code
- [ ] No secrets committed to version control

### Data Exposure
- [ ] No PII (Personally Identifiable Information) in logs
- [ ] Sensitive data encrypted at rest
- [ ] Sensitive data encrypted in transit (HTTPS/TLS)
- [ ] No stack traces exposed in production
- [ ] Error messages don't leak system information
- [ ] No debug endpoints in production

### API Security
- [ ] Rate limiting on public endpoints
- [ ] Request size limits
- [ ] Timeout on long-running operations
- [ ] No sensitive data in URL parameters
- [ ] Proper CORS configuration
- [ ] API versioning in place

### Dependency Security
- [ ] Dependencies are up to date
- [ ] No known vulnerabilities in dependencies
- [ ] Minimal dependencies (reduce attack surface)
- [ ] Verify package integrity (checksums)

---

## Common Vulnerabilities & Fixes

### SQL Injection

**Vulnerable:**
```python
# NEVER DO THIS
query = f"SELECT * FROM users WHERE email = '{email}'"
cursor.execute(query)
```

**Secure:**
```python
# Use parameterized queries
query = "SELECT * FROM users WHERE email = ?"
cursor.execute(query, (email,))

# Or use ORM
user = db.query(User).filter(User.email == email).first()
```

### XSS (Cross-Site Scripting)

**Vulnerable:**
```javascript
// NEVER DO THIS
element.innerHTML = userInput;
document.write(userInput);
eval(userInput);
```

**Secure:**
```javascript
// Use textContent or framework escaping
element.textContent = userInput;

// In React
<div>{userInput}</div>  // automatically escaped

// If HTML is needed, sanitize first
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

### Hardcoded Secrets

**Vulnerable:**
```python
# NEVER DO THIS
DATABASE_URL = "postgresql://user:password@localhost/db"
API_KEY = "sk_live_abc123xyz"
SECRET_KEY = "my-secret-key-123"
```

**Secure:**
```python
# Load from environment
import os

DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

# Validate they exist
if not all([DATABASE_URL, API_KEY, SECRET_KEY]):
    raise ValueError("Required environment variables not set")
```

### Insecure Password Storage

**Vulnerable:**
```python
# NEVER DO THIS
user.password = password  # plain text
user.password = hashlib.md5(password.encode()).hexdigest()  # weak hash
```

**Secure:**
```python
# Use bcrypt or argon2
import bcrypt

hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
user.password_hash = hashed.decode()

# Verify
if bcrypt.checkpw(password.encode(), user.password_hash.encode()):
    # password correct
```

### Path Traversal

**Vulnerable:**
```python
# NEVER DO THIS
file_path = f"/uploads/{user_filename}"
with open(file_path, 'r') as f:
    content = f.read()
```

**Secure:**
```python
import os
from pathlib import Path

# Validate and sanitize filename
safe_filename = Path(user_filename).name  # removes path components
file_path = Path("/uploads") / safe_filename

# Ensure it's within allowed directory
if not file_path.resolve().is_relative_to(Path("/uploads").resolve()):
    raise ValueError("Invalid file path")

with open(file_path, 'r') as f:
    content = f.read()
```

### Insecure Deserialization

**Vulnerable:**
```python
# NEVER DO THIS
import pickle
data = pickle.loads(user_input)  # can execute arbitrary code
```

**Secure:**
```python
# Use safe formats like JSON
import json
data = json.loads(user_input)

# Or use safe serialization libraries
from pydantic import BaseModel

class UserData(BaseModel):
    name: str
    email: str

data = UserData.parse_raw(user_input)
```

### Missing Authorization

**Vulnerable:**
```python
# NEVER DO THIS
@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    return db.query(User).filter(User.id == user_id).first()
```

**Secure:**
```python
@app.get("/api/users/{user_id}")
def get_user(user_id: int, current_user: User = Depends(get_current_user)):
    # Check authorization
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return db.query(User).filter(User.id == user_id).first()
```

---

## Logging Security

### What NOT to Log
- Passwords (plain or hashed)
- API keys, tokens, secrets
- Credit card numbers, CVV
- Social security numbers
- Session IDs
- Personal health information
- Full request/response bodies (may contain sensitive data)

### Safe Logging
```python
# Bad
logger.info(f"User login: {username} password: {password}")
logger.info(f"API call with key: {api_key}")
logger.error(f"Payment failed: {credit_card_number}")

# Good
logger.info(f"User login attempt: {username}")
logger.info(f"API call authenticated")
logger.error(f"Payment failed for user: {user_id}")

# Mask sensitive data if needed
masked_card = f"****-****-****-{credit_card_number[-4:]}"
logger.info(f"Payment processed: {masked_card}")
```

---

## Security Headers (Web Applications)

```python
# Add security headers to all responses
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
response.headers["Content-Security-Policy"] = "default-src 'self'"
```

---

## When to Escalate

If you find any of these, mark as CRITICAL and REJECT:
- Hardcoded credentials or API keys
- SQL injection vulnerability
- Missing authentication on sensitive endpoints
- Passwords stored in plain text
- Secrets in logs
- Arbitrary code execution vulnerability

For other security issues, mark as NEEDS_REVISION with clear remediation steps.
