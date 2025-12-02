# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of OxUtils seriously. If you discover a security vulnerability, please follow these steps:

### 1. **Do Not** Open a Public Issue

Please do not report security vulnerabilities through public GitHub issues.

### 2. Report Privately

Send an email to **eddycondor07@gmail.com** with:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - Critical: 1-7 days
  - High: 7-14 days
  - Medium: 14-30 days
  - Low: 30-90 days

### 4. Disclosure Policy

- We will acknowledge receipt of your report
- We will confirm the vulnerability and determine its impact
- We will release a fix as soon as possible
- We will publicly disclose the vulnerability after a fix is released
- We will credit you in the security advisory (unless you prefer to remain anonymous)

## Security Best Practices

When using OxUtils:

### JWT Authentication
- Always use HTTPS in production
- Store JWT tokens in httpOnly cookies, not localStorage
- Set short expiration times (15 minutes recommended)
- Rotate keys regularly
- Use JWKS for key distribution in microservices

### S3 Storage
- Use private ACLs for sensitive data
- Enable bucket encryption
- Use presigned URLs for private content
- Implement proper IAM policies
- Enable S3 bucket logging

### Secrets Management
- Never commit secrets to version control
- Use environment variables for all sensitive data
- Use AWS Secrets Manager or similar for production
- Rotate credentials regularly

### Audit Logging
- Enable `OXI_LOG_ACCESS` for compliance
- Set appropriate `OXI_RETENTION_DELAY`
- Regularly review audit logs
- Export logs to secure storage

## Known Security Considerations

### JWT Token Storage
OxUtils provides JWT verification but does not handle token storage. Implement secure storage in your application.

### S3 Presigned URLs
Private media URLs are valid for 1 hour by default. Adjust if needed for your use case.

### Exception Details
In production, avoid exposing detailed error messages to end users. Use `DEBUG=False` in Django.

## Security Updates

Security updates will be released as patch versions and documented in [CHANGELOG.md](CHANGELOG.md).

Subscribe to releases on GitHub to be notified of security updates.

## Contact

For security concerns: **eddycondor07@gmail.com**

For general issues: [GitHub Issues](https://github.com/oxiliere/oxutils/issues)
