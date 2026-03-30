"""Core sync logic: WeCom → LDAP."""
import logging

from app.config import settings
from app.ldap_client import LDAPClient
from app.wecom import WeComClient

logger = logging.getLogger(__name__)


def build_department_tree(departments: list[dict]) -> dict[int, dict]:
    """Index departments by id."""
    by_id: dict[int, dict] = {}
    for d in departments:
        by_id[d["id"]] = {
            "id": d["id"],
            "name": d["name"],
            "parentid": d.get("parentid", 0),
        }
    return by_id


def department_ou_dn(dept_id: int, dept_map: dict[int, dict], ldap: LDAPClient) -> str:
    """Recursively ensure the OU chain exists and return the leaf OU DN.

    WeCom department 1 is the root corp and maps to the people OU.
    """
    dept = dept_map.get(dept_id)
    if not dept or dept_id == 1:
        return ldap.ensure_ou(settings.ldap_user_ou)

    parent_dn = department_ou_dn(dept["parentid"], dept_map, ldap)
    return ldap.ensure_ou(dept["name"], parent_dn)


def run_sync():
    """Execute one full sync cycle."""
    ldap = LDAPClient()
    wecom = WeComClient()

    stats = {"departments": 0, "created": 0, "updated": 0, "deleted": 0}

    try:
        ldap.connect()

        # 1. Fetch WeCom data
        departments = wecom.get_departments()
        dept_map = build_department_tree(departments)
        users = wecom.get_all_users()

        # 2. Ensure OU structure
        for dept in departments:
            department_ou_dn(dept["id"], dept_map, ldap)
            stats["departments"] += 1

        # 3. Get existing LDAP users for move/orphan detection
        existing_users = ldap.get_all_user_uids()

        # 4. Sync users
        synced_uids: set[str] = set()
        for user in users:
            userid = user["userid"]
            synced_uids.add(userid)

            primary_dept = user.get("main_department") or user.get("department", [1])[0]
            ou_dn = department_ou_dn(primary_dept, dept_map, ldap)

            if settings.dry_run:
                logger.info("[DRY RUN] Would sync user %s to %s", userid, ou_dn)
                continue

            expected_dn = f"uid={userid},{ou_dn}"
            old_dn = existing_users.get(userid)

            # User moved departments — delete old entry first
            if old_dn and old_dn != expected_dn:
                ldap.delete_user(old_dn)
                logger.info("User %s moved from %s to %s", userid, old_dn, expected_dn)

            changed = ldap.upsert_user(user, ou_dn)
            if changed:
                if old_dn:
                    stats["updated"] += 1
                else:
                    stats["created"] += 1

        # 6. Sync department-based groups (groupOfNames)
        groups_ou = ldap.ensure_groups_ou()
        dept_members: dict[str, list[str]] = {}  # dept_name -> [user_dn]
        for user in users:
            userid = user["userid"]
            primary_dept = user.get("main_department") or user.get("department", [1])[0]
            dept = dept_map.get(primary_dept)
            dept_name = dept["name"] if dept and primary_dept != 1 else settings.ldap_user_ou
            ou_dn = department_ou_dn(primary_dept, dept_map, ldap)
            user_dn = f"uid={userid},{ou_dn}"
            dept_members.setdefault(dept_name, []).append(user_dn)

        synced_groups: set[str] = set()
        for dept_name, members in dept_members.items():
            synced_groups.add(dept_name)
            if not settings.dry_run:
                ldap.upsert_group(dept_name, members, groups_ou)

        # Remove orphaned groups
        if settings.sync_delete_orphans and not settings.dry_run:
            existing_groups = ldap.get_all_groups(groups_ou)
            for cn, dn in existing_groups.items():
                if cn not in synced_groups:
                    ldap.delete_entry(dn)
                    logger.info("Deleted orphan group: %s", cn)

        # 6. Optionally remove orphaned LDAP users
        if settings.sync_delete_orphans and not settings.dry_run:
            for uid, dn in existing_users.items():
                if uid not in synced_uids:
                    ldap.delete_user(dn)
                    stats["deleted"] += 1
                    logger.info("Deleted orphan user: %s (%s)", uid, dn)

        logger.info(
            "Sync completed: %d depts, %d created, %d updated, %d deleted",
            stats["departments"], stats["created"], stats["updated"], stats["deleted"],
        )

    except Exception:
        logger.exception("Sync failed")
        raise
    finally:
        ldap.disconnect()
