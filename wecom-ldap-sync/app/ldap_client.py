"""LDAP operations for syncing WeCom data."""
import hashlib
import logging
import os

from ldap3 import (
    ALL,
    MODIFY_REPLACE,
    Connection,
    Server,
    SUBTREE,
)

from app.config import settings

logger = logging.getLogger(__name__)


class LDAPClient:
    def __init__(self):
        self._server = Server(
            f"ldap://{settings.ldap_host}:{settings.ldap_port}",
            get_info=ALL,
        )
        self._conn: Connection | None = None

    def connect(self):
        self._conn = Connection(
            self._server,
            user=settings.ldap_admin_dn,
            password=settings.ldap_admin_password,
            auto_bind=True,
        )
        logger.info("Connected to LDAP server %s", settings.ldap_host)

    def disconnect(self):
        if self._conn:
            self._conn.unbind()
            self._conn = None

    @property
    def conn(self) -> Connection:
        if not self._conn or self._conn.closed:
            self.connect()
        return self._conn

    # ── OU (department) operations ──────────────────────────────────────

    def ensure_ou(self, ou_name: str, parent_dn: str | None = None) -> str:
        """Create an OU if it doesn't exist. Returns the full DN."""
        parent = parent_dn or settings.ldap_base_dn
        dn = f"ou={ou_name},{parent}"
        if self._entry_exists(dn):
            return dn
        self.conn.add(dn, "organizationalUnit", {"ou": ou_name})
        if self.conn.result["result"] == 0:
            logger.info("Created OU: %s", dn)
        else:
            logger.warning("Failed to create OU %s: %s", dn, self.conn.result)
        return dn

    # ── User operations ─────────────────────────────────────────────────

    def upsert_user(self, user: dict, ou_dn: str) -> bool:
        """Create or update an inetOrgPerson from WeCom user data.

        Args:
            user: WeCom user dict (userid, name, mobile, email, position, etc.)
            ou_dn: The DN of the OU (department) the user belongs to.

        Returns:
            True if a change was made, False otherwise.
        """
        userid = user["userid"]
        dn = f"uid={userid},{ou_dn}"
        attrs = self._wecom_user_to_ldap_attrs(user)

        if self._entry_exists(dn):
            return self._update_user(dn, attrs)
        else:
            return self._create_user(dn, attrs)

    def _wecom_user_to_ldap_attrs(self, user: dict) -> dict:
        """Map WeCom user fields to LDAP attributes.
        Works with both simplelist (userid, name) and full user/get data.
        """
        name = user.get("name", user["userid"])

        # Split name: use first char as sn, rest as givenName (best-effort for CJK)
        sn = name[0] if name else user["userid"]
        given_name = name[1:] if len(name) > 1 else name

        attrs = {
            "cn": name,
            "sn": sn,
            "givenName": given_name,
            "uid": user["userid"],
            "displayName": name,
            "employeeNumber": user["userid"],
        }

        # Email: use WeCom email if available, otherwise generate from uid + suffix
        if user.get("email"):
            attrs["mail"] = user["email"]
        elif settings.email_suffix:
            attrs["mail"] = f"{user['userid']}{settings.email_suffix}"
        if user.get("mobile"):
            attrs["mobile"] = user["mobile"]
        if user.get("position"):
            attrs["title"] = user["position"]
        if user.get("gender"):
            # WeCom: 1=male, 2=female, 0=undefined
            gender_map = {"1": "M", "2": "F"}
            attrs["initials"] = gender_map.get(str(user["gender"]), "")
        if user.get("department"):
            attrs["departmentNumber"] = [str(d) for d in user["department"]]
        attrs["employeeNumber"] = user["userid"]

        return attrs

    @staticmethod
    def _ssha_hash(password: str) -> bytes:
        """Generate an SSHA hash for the given password."""
        salt = os.urandom(16)
        digest = hashlib.sha1(password.encode("utf-8") + salt).digest()
        import base64
        return b"{SSHA}" + base64.b64encode(digest + salt)

    def _create_user(self, dn: str, attrs: dict) -> bool:
        object_classes = ["inetOrgPerson", "organizationalPerson", "person", "top"]
        if settings.ldap_default_password:
            attrs["userPassword"] = self._ssha_hash(settings.ldap_default_password)
        self.conn.add(dn, object_classes, attrs)
        if self.conn.result["result"] == 0:
            logger.info("Created user: %s", dn)
            return True
        logger.warning("Failed to create user %s: %s", dn, self.conn.result)
        return False

    def _update_user(self, dn: str, attrs: dict) -> bool:
        changes = {k: [(MODIFY_REPLACE, [v] if not isinstance(v, list) else v)]
                   for k, v in attrs.items()}
        self.conn.modify(dn, changes)
        if self.conn.result["result"] == 0:
            logger.debug("Updated user: %s", dn)
            return True
        logger.warning("Failed to update user %s: %s", dn, self.conn.result)
        return False

    def delete_user(self, dn: str) -> bool:
        self.conn.delete(dn)
        if self.conn.result["result"] == 0:
            logger.info("Deleted user: %s", dn)
            return True
        logger.warning("Failed to delete user %s: %s", dn, self.conn.result)
        return False

    def get_all_user_uids(self, base_dn: str | None = None) -> dict[str, str]:
        """Return {uid: dn} for all users under the base.

        Searches under the people OU to avoid touching system entries.
        """
        search_base = base_dn or settings.ldap_base_dn
        self.conn.search(
            search_base,
            "(objectClass=inetOrgPerson)",
            search_scope=SUBTREE,
            attributes=["uid"],
        )
        result = {}
        for entry in self.conn.entries:
            uid = str(entry.uid) if hasattr(entry, "uid") else None
            if uid:
                result[uid] = str(entry.entry_dn)
        return result

    # ── Group operations ─────────────────────────────────────────────────

    def ensure_groups_ou(self) -> str:
        """Ensure ou=groups exists under base DN."""
        return self.ensure_ou("groups")

    def upsert_group(self, group_name: str, member_dns: list[str], groups_ou: str) -> bool:
        """Create or update a groupOfNames entry.

        groupOfNames requires at least one member, so if member_dns is empty
        we use the admin DN as a placeholder.
        """
        dn = f"cn={group_name},{groups_ou}"
        members = member_dns if member_dns else [settings.ldap_admin_dn]

        if self._entry_exists(dn):
            changes = {"member": [(MODIFY_REPLACE, members)]}
            self.conn.modify(dn, changes)
            if self.conn.result["result"] == 0:
                logger.debug("Updated group: %s (%d members)", group_name, len(member_dns))
                return True
            logger.warning("Failed to update group %s: %s", dn, self.conn.result)
            return False
        else:
            attrs = {"cn": group_name, "member": members}
            self.conn.add(dn, "groupOfNames", attrs)
            if self.conn.result["result"] == 0:
                logger.info("Created group: %s (%d members)", group_name, len(member_dns))
                return True
            logger.warning("Failed to create group %s: %s", dn, self.conn.result)
            return False

    def get_all_groups(self, groups_ou: str) -> dict[str, str]:
        """Return {cn: dn} for all groupOfNames under groups OU."""
        self.conn.search(
            groups_ou,
            "(objectClass=groupOfNames)",
            search_scope=SUBTREE,
            attributes=["cn"],
        )
        result = {}
        for entry in self.conn.entries:
            cn = str(entry.cn) if hasattr(entry, "cn") else None
            if cn:
                result[cn] = str(entry.entry_dn)
        return result

    def delete_entry(self, dn: str) -> bool:
        self.conn.delete(dn)
        if self.conn.result["result"] == 0:
            logger.info("Deleted entry: %s", dn)
            return True
        logger.warning("Failed to delete %s: %s", dn, self.conn.result)
        return False

    def set_default_password_for_all_users(self) -> int:
        """Set the default password on all existing users that lack one.

        Returns the number of users updated.
        """
        if not settings.ldap_default_password:
            logger.warning("No default password configured, skipping")
            return 0

        search_base = f"ou={settings.ldap_user_ou},{settings.ldap_base_dn}"
        self.conn.search(
            search_base,
            "(&(objectClass=inetOrgPerson)(!(userPassword=*)))",
            search_scope=SUBTREE,
            attributes=["uid"],
        )
        count = 0
        hashed = self._ssha_hash(settings.ldap_default_password)
        for entry in self.conn.entries:
            dn = str(entry.entry_dn)
            self.conn.modify(dn, {"userPassword": [(MODIFY_REPLACE, [hashed])]})
            if self.conn.result["result"] == 0:
                logger.info("Set default password for: %s", dn)
                count += 1
            else:
                logger.warning("Failed to set password for %s: %s", dn, self.conn.result)
        return count

    # ── Helpers ──────────────────────────────────────────────────────────

    def _entry_exists(self, dn: str) -> bool:
        try:
            self.conn.search(dn, "(objectClass=*)", search_scope="BASE")
            return len(self.conn.entries) > 0
        except Exception:
            return False
