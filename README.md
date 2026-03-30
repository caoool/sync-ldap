# WeCom → LDAP Sync

Sync your WeCom (企业微信) contacts into OpenLDAP automatically. Runs as a Docker service alongside OpenLDAP and phpLDAPadmin.

## What it does

- Pulls departments and users from WeCom via a self-built app (自建应用) with contacts read permission
- Creates a matching OU hierarchy in LDAP
- Syncs user attributes: name, position, alias, department, email
- Runs on a configurable schedule (default: every 30 minutes)
- Optionally removes LDAP users no longer in WeCom

## Quick Start

### WeCom Setup

1. Go to [WeCom Admin Console](https://work.weixin.qq.com/wework_admin/frame)
2. **我的企业 → 企业信息** → copy **企业ID** → `WECOM_CORPID`
3. **应用管理 → 自建** → create an app → grant **可见范围** permission → copy **Secret** → `WECOM_CORPSECRET`
4. Add your server IP to the app's **企业可信IP** list

### Start Sync

```bash
cp .env.example .env
# Edit .env with your LDAP and WeCom settings
docker compose up -d
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| OpenLDAP | 389 | LDAP server |
| wecom-ldap-sync | — | Sync service (no exposed port) |

## Limitations

- **No native email or mobile from WeCom**: WeCom classifies these as sensitive fields, only available for verified orgs (已验证企业). As a workaround, set `EMAIL_SUFFIX` (e.g. `@example.com`) to auto-generate email as `uid@example.com`. Leave blank to skip. If WeCom does return a real email, it takes priority.
- **Odd userids**: Some WeCom accounts may have email-style or phone-number userids (e.g. `user@company.com`, `186xxxx`) set by the admin who created them. These are used as-is for the LDAP `uid`.

## Roadmap

- [ ] DingTalk (钉钉) sync support
- [ ] Feishu (飞书) sync support
- [ ] Multi-source merge (sync from multiple platforms into one LDAP)
