# WeCom → LDAP Sync · 企业微信通讯录同步到 LDAP

[![Docker Hub](https://img.shields.io/docker/pulls/caoool/wecom-ldap-sync?label=docker%20pulls)](https://hub.docker.com/r/caoool/wecom-ldap-sync)
[![License](https://img.shields.io/github/license/caoool/sync-ldap)](LICENSE)

🌐 **Landing page / 项目主页:** <https://caoool.github.io/sync-ldap/>

📖 **Languages:** [English](#english) · [中文](#中文)

### Project links

- [Architecture notes](docs/architecture.md): data flow, runtime components, LDAP writes, and security notes.
- [Promotion kit](docs/promotion.md): launch posts, Docker Hub copy, GitHub topics, and community checklist.
- [Changelog](CHANGELOG.md): notable documentation and release changes.

---

## English

Sync your WeCom (企业微信) contacts into OpenLDAP automatically. Runs as a Docker service alongside an OpenLDAP container.

### What it does

- Pulls departments and users from WeCom via a self-built app (自建应用) with contacts read permission
- Creates a matching OU hierarchy in LDAP
- Syncs user attributes: name, position, alias, department, email
- Sets a configurable default password (SSHA-hashed) for new users and existing users that lack one
- Runs on a configurable schedule (default: every 30 minutes)
- Optionally removes LDAP users no longer in WeCom

### Quick Start

#### 1. WeCom Setup

1. Go to the [WeCom Admin Console](https://work.weixin.qq.com/wework_admin/frame)
2. **我的企业 → 企业信息** → copy **企业ID** → `WECOM_CORPID`
3. **应用管理 → 自建** → create an app → grant **通讯录** (contacts read) permission → copy **Secret** → `WECOM_CORPSECRET`
4. Add your server's public IP to the app's **企业可信IP** list

#### 2. Start Sync

```bash
cp .env.example .env
# Edit .env with your LDAP and WeCom settings
docker compose up -d
```

The sync runs once on startup, then on the configured interval. Tail logs with:

```bash
docker compose logs -f wecom-ldap-sync
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| `openldap` | 389 (LDAP), 636 (LDAPS) | OpenLDAP server |
| `wecom-ldap-sync` | — | Sync worker (no exposed port) |

### Configuration

Key variables (see `.env.example` for the full list):

| Variable | Default | Description |
|----------|---------|-------------|
| `LDAP_DOMAIN` | `ldap.example.com` | Domain used by openldap to derive the base DN |
| `LDAP_BASE_DN` | `dc=ldap,dc=example,dc=com` | Base DN — must match `LDAP_DOMAIN` |
| `LDAP_ADMIN_PASSWORD` | `changeme` | LDAP admin password (change this!) |
| `LDAP_USER_OU` | `people` | OU under base DN where synced users live |
| `LDAP_DEFAULT_PASSWORD` | `changeme` | SSHA-hashed password set on new users and on existing users without a password. Not overwritten if the user already has one. |
| `EMAIL_SUFFIX` | `@example.com` | Auto-generates email as `uid@example.com`. Leave blank to skip. Real WeCom email takes priority when present. |
| `WECOM_CORPID` | — | Corp ID from 我的企业 → 企业信息 |
| `WECOM_CORPSECRET` | — | Self-built app Secret |
| `SYNC_INTERVAL_MINUTES` | `30` | How often to re-sync |
| `SYNC_DELETE_ORPHANS` | `true` | Delete LDAP users no longer in WeCom (use with caution) |
| `DRY_RUN` | `false` | Preview changes without writing to LDAP |

### Limitations

- **No native email or mobile from WeCom**: WeCom classifies these as sensitive fields, only available for verified orgs (已验证企业). As a workaround, set `EMAIL_SUFFIX` to auto-generate email as `uid@example.com`. If WeCom does return a real email, it takes priority.
- **Odd userids**: Some WeCom accounts may have email-style or phone-number userids (e.g. `user@company.com`, `186xxxx`) set by the admin who created them. These are used as-is for the LDAP `uid`.

### Roadmap

- [ ] DingTalk (钉钉) sync support
- [ ] Feishu (飞书) sync support
- [ ] Multi-source merge (sync from multiple platforms into one LDAP)

### Feedback wanted

If you run WeCom with OpenLDAP, SSO, VPN, or self-hosted internal apps, feedback is welcome. Useful reports include missing LDAP attributes, sync edge cases, deployment notes, and whether DingTalk or Feishu support should come next.

---

## 中文

将企业微信通讯录自动同步到 OpenLDAP。以 Docker 服务形式运行，与 OpenLDAP 容器一同启动。

### 功能

- 通过企业微信「自建应用」（需通讯录读取权限）拉取部门与成员
- 在 LDAP 中创建对应的 OU 组织结构
- 同步用户属性：姓名、职位、别名、部门、邮箱
- 为新用户（及缺失密码的旧用户）设置可配置的默认密码（SSHA 加密）
- 按可配置周期自动同步（默认每 30 分钟）
- 可选：删除企业微信中已不存在的 LDAP 用户

### 快速开始

#### 1. 企业微信配置

1. 进入 [企业微信管理后台](https://work.weixin.qq.com/wework_admin/frame)
2. **我的企业 → 企业信息** → 复制 **企业ID** → 填入 `WECOM_CORPID`
3. **应用管理 → 自建** → 新建应用 → 授予 **通讯录** 读取权限 → 复制 **Secret** → 填入 `WECOM_CORPSECRET`
4. 将服务器的公网 IP 加入应用的 **企业可信IP** 列表

#### 2. 启动同步

```bash
cp .env.example .env
# 编辑 .env，填入 LDAP 与企微相关配置
docker compose up -d
```

服务启动时立即跑一次同步，之后按配置周期循环。查看日志：

```bash
docker compose logs -f wecom-ldap-sync
```

### 服务列表

| 服务 | 端口 | 说明 |
|------|------|------|
| `openldap` | 389 (LDAP)、636 (LDAPS) | OpenLDAP 服务端 |
| `wecom-ldap-sync` | — | 同步进程（不暴露端口） |

### 配置项

主要变量（完整列表见 `.env.example`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LDAP_DOMAIN` | `ldap.example.com` | openldap 据此推导 base DN 的域名 |
| `LDAP_BASE_DN` | `dc=ldap,dc=example,dc=com` | Base DN，需与 `LDAP_DOMAIN` 对应 |
| `LDAP_ADMIN_PASSWORD` | `changeme` | LDAP 管理员密码（务必修改！） |
| `LDAP_USER_OU` | `people` | 同步用户所在的 OU |
| `LDAP_DEFAULT_PASSWORD` | `changeme` | 新用户的默认密码（SSHA 加密）；对已存在但无密码的用户也会补设；已设置密码的用户不会被覆盖 |
| `EMAIL_SUFFIX` | `@example.com` | 自动生成邮箱 `uid@example.com`，留空则不生成；企微返回的真实邮箱优先 |
| `WECOM_CORPID` | — | 我的企业 → 企业信息 → 企业ID |
| `WECOM_CORPSECRET` | — | 自建应用的 Secret |
| `SYNC_INTERVAL_MINUTES` | `30` | 同步周期（分钟） |
| `SYNC_DELETE_ORPHANS` | `true` | 删除企微中已不存在的 LDAP 用户（谨慎使用） |
| `DRY_RUN` | `false` | 仅预览，不写入 LDAP |

### 已知限制

- **企微不直接返回邮箱/手机号**：这两个字段属于敏感信息，仅对「已验证企业」开放。可通过 `EMAIL_SUFFIX` 自动生成 `uid@your-domain.com` 作为变通；若企微返回了真实邮箱则以真实值为准。
- **特殊 userid**：部分账号在企微后台被管理员设为邮箱或手机号形式（如 `user@company.com`、`186xxxx`），同步时会原样作为 LDAP `uid` 使用。

### 路线图

- [ ] 钉钉（DingTalk）同步支持
- [ ] 飞书（Feishu）同步支持
- [ ] 多源合并（多个平台同步到同一 LDAP）

### 欢迎反馈

如果你正在把企业微信与 OpenLDAP、SSO、VPN 或自托管内部系统一起使用，欢迎反馈真实场景。特别需要了解：缺失的 LDAP 字段、同步边界情况、部署问题，以及钉钉/飞书支持的优先级。
