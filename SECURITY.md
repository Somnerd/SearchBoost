# Security Policy

The SearchBoost team takes the security of our software and users seriously. We appreciate responsible disclosure of security vulnerabilities.

---

## 🛡️ Supported Versions

We provide security updates and patches for the following versions:

| Version | Supported | Notes |
| :--- | :---: | :--- |
| `1.0.x` | ✅ | Active release line |
| `< 1.0` | ❌ | Pre-release versions |

---

## 🚨 Reporting a Vulnerability

If you discover a security vulnerability in SearchBoost, please **do not open a public issue**. Instead, follow these steps:

1. **Email Advisory**: Send details of the vulnerability to `security@somnerd.com` (or submit a Private Vulnerability Report directly through GitHub via **Security** -> **Advisories** -> **Report a vulnerability**).
2. **Provide Details**:
   - Description of the vulnerability and its potential impact.
   - Step-by-step reproduction steps or proof-of-concept (PoC).
   - Affected system tier (API, Worker, Warden, or UI).
   - Any suggested remediations or patches.
3. **Response Timeline**:
   - **Acknowledgment**: Within 48 hours.
   - **Assessment & Triage**: Within 5 business days.
   - **Patch Release**: Coordinated with the reporter before public disclosure.

---

## 🔒 Security Invariants & Design Principles

* **IDOR Protection**: All search job lookups and session retrievals strictly validate ownership (`user_id = session.user.id`).
* **Role-Based Access Control (RBAC)**: Admin routes are protected by JWT verification and role checks (`req.user.role === 'admin'`). System admins cannot self-demote or delete their own accounts.
* **Separation of Privacy Concerns**: SearchBoost does not process or tokenize PII locally. Upstream masking is handled by IronWarden before reaching the search synthesis fleet.
* **Container Isolation**: Multi-stage Docker images run as unprivileged non-root users (`node:node` and `nginx:101`).
