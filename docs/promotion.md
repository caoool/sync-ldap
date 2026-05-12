# Promotion Kit

This file collects reusable copy and a launch checklist for promoting `wecom-ldap-sync`.

## One-Line Pitch

English:

> Sync WeCom (企业微信) contacts into OpenLDAP with Docker for self-hosted SSO and unified identity management.

中文:

> 用 Docker 将企业微信通讯录自动同步到 OpenLDAP，适合自托管 SSO、统一身份认证和内部账号目录管理。

## Short Description

English:

`wecom-ldap-sync` is an open-source Docker service that mirrors your WeCom directory into OpenLDAP. It syncs departments, users, common user attributes, generated emails, and default LDAP passwords on a configurable schedule.

中文:

`wecom-ldap-sync` 是一个开源 Docker 服务，用于把企业微信通讯录同步到 OpenLDAP。它会按配置周期同步部门、用户、常用用户属性、自动生成邮箱和默认 LDAP 密码。

## Launch Post

### English

I built `wecom-ldap-sync`, a small open-source Docker service for teams that use WeCom (企业微信) internally but still need an LDAP directory for SSO, VPN, internal apps, or legacy tools.

It reads departments and users from a WeCom self-built app, creates the matching OU hierarchy in LDAP, syncs common user attributes, and runs on a configurable interval. New LDAP users get an SSHA-hashed default password, and existing user passwords are not overwritten.

Why I built it:

- Many self-hosted tools still speak LDAP.
- WeCom is common in Chinese teams, but keeping LDAP users in sync manually is tedious.
- I wanted something simple enough to run with Docker Compose and inspect through logs.

What it supports today:

- WeCom departments and users
- OpenLDAP
- Dry-run mode
- Optional orphan cleanup
- Email fallback with `EMAIL_SUFFIX`
- Bilingual docs

Links:

- GitHub: https://github.com/caoool/sync-ldap
- Landing page: https://caoool.github.io/sync-ldap/
- Docker Hub: https://hub.docker.com/r/caoool/wecom-ldap-sync

I am looking for feedback from people running WeCom, OpenLDAP, SSO, VPN, or self-hosted internal tools.

### 中文

我做了一个小工具：`wecom-ldap-sync`，用于把企业微信通讯录自动同步到 OpenLDAP。

适合这样的场景：公司内部用企业微信管理员工和组织架构，但 VPN、SSO、内部系统、老系统或一些自托管工具仍然需要 LDAP 目录。

它通过企业微信「自建应用」读取部门和成员，在 LDAP 中创建对应 OU 结构，同步用户属性，并按配置周期自动运行。新用户会设置 SSHA 加密的默认密码，已有密码不会被覆盖。

目前支持：

- 同步企业微信部门和成员
- 写入 OpenLDAP
- Dry-run 预览模式
- 可选删除离职/不存在用户
- 通过 `EMAIL_SUFFIX` 自动补邮箱
- 中英文文档

项目地址：

- GitHub: https://github.com/caoool/sync-ldap
- 项目主页: https://caoool.github.io/sync-ldap/
- Docker Hub: https://hub.docker.com/r/caoool/wecom-ldap-sync

如果你正在使用企业微信、OpenLDAP、SSO、VPN 或自托管内部系统，欢迎试用和反馈。

## Docker Hub Copy

Short description:

> Sync WeCom (企业微信) contacts into OpenLDAP with Docker.

Full description:

> Open-source Docker service that mirrors your WeCom directory into OpenLDAP. It syncs departments, users, common LDAP attributes, generated emails, and default passwords on a configurable schedule. Designed for self-hosted SSO, VPN, internal tools, and unified identity management.

## Suggested GitHub Topics

Current repository topics:

`wecom`, `ldap`, `openldap`, `docker`, `self-hosted`, `sso`, `identity-management`, `directory-sync`, `wecom-ldap`, `enterprise-wechat`, `ldap-sync`, `dingtalk`, `feishu`, `docker-compose`, `python`

## Launch Checklist

- [x] Add GitHub repository topics.
- [x] Create a GitHub release with release notes: https://github.com/caoool/sync-ldap/releases/tag/v0.1.0
- [x] Update Docker Hub description using the copy above: https://hub.docker.com/r/caoool/wecom-ldap-sync
- [x] Open feedback issues for DingTalk, Feishu, and extra LDAP attribute mappings:
  - https://github.com/caoool/sync-ldap/issues/2
  - https://github.com/caoool/sync-ldap/issues/3
  - https://github.com/caoool/sync-ldap/issues/4
  - https://github.com/caoool/sync-ldap/issues/5
- [ ] Post the Chinese launch note to V2EX, 开源中国, 掘金, SegmentFault, and relevant WeCom/self-hosted groups.
- [ ] Post the English launch note to r/selfhosted, r/devops, Hacker News Show HN, and relevant LDAP/SSO communities.
- [ ] Ask explicitly for testers using WeCom plus OpenLDAP.

## Feedback Prompt

Use this sentence at the end of posts:

> If you use WeCom with LDAP, SSO, VPN, or self-hosted internal apps, I would like to know which LDAP attributes and edge cases matter in your setup.
