"""Concrete implementation of the Ticket API that talks to Jira Cloud."""

from __future__ import annotations

import logging
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import httpx

from ticket_api import (
    Comment,
    ServiceError,
    Ticket,
    TicketNotFoundError,
    TicketPriority,
    TicketServiceAPI,
    TicketStatus,
)

from . import jira_client as jc
from .storage import ensure_mapping_for_keys, get_key_for_uuid, map_uuid_to_key

logger = logging.getLogger(__name__)

# ---- mapping helpers ----


def _priority_to_jira(p: TicketPriority) -> str:
    return {
        TicketPriority.LOW: "Low",
        TicketPriority.MEDIUM: "Medium",
        TicketPriority.HIGH: "High",
        TicketPriority.CRITICAL: "Highest",
    }[p]


def _status_name_to_domain(name: str | None) -> TicketStatus:
    if not name:
        return TicketStatus.OPEN
    k = name.strip().lower().replace("-", "_").replace(" ", "_")
    if k in {"open", "to_do"}:
        return TicketStatus.OPEN
    if k in {"in_progress", "doing"}:
        return TicketStatus.IN_PROGRESS
    if k in {"done", "resolved"}:
        return TicketStatus.RESOLVED
    if k == "closed":
        return TicketStatus.CLOSED
    return TicketStatus.OPEN


def _jira_to_ticket(data: dict[str, Any], user_id: str) -> Ticket:
    fields = data.get("fields", {})
    key = data.get("key", "")
    status_name = (fields.get("status") or {}).get("name")
    priority_name = (fields.get("priority") or {}).get("name", "Medium")

    # domain priority best-effort reverse map
    pr_map = {
        "low": TicketPriority.LOW,
        "medium": TicketPriority.MEDIUM,
        "high": TicketPriority.HIGH,
        "highest": TicketPriority.CRITICAL,
    }
    domain_priority = pr_map.get(str(priority_name).lower(), TicketPriority.MEDIUM)

    # stable UUID for this user+key; also store mapping (impl never leaks Jira key)
    ticket_uuid = uuid5(NAMESPACE_URL, f"{user_id}:{key}")
    map_uuid_to_key(user_id, ticket_uuid, key)

    return Ticket(
        id=ticket_uuid,
        title=fields.get("summary", ""),
        description=(fields.get("description") or "")
        if isinstance(fields.get("description"), str)
        else str(fields.get("description") or ""),
        status=_status_name_to_domain(status_name),
        priority=domain_priority,
        assignee=(fields.get("assignee") or {}).get("displayName"),
        reporter=(fields.get("reporter") or {}).get("displayName") or "",
    )


def _jira_comment_to_domain(c: dict[str, Any], ticket_uuid: UUID) -> Comment:
    text = ""
    body = c.get("body") or {}
    if isinstance(body, dict):
        for block in body.get("content", []):
            if block.get("type") == "paragraph":
                for node in block.get("content", []):
                    if node.get("type") == "text":
                        text += node.get("text", "")
                text += "\n"
    return Comment(
        id=uuid5(NAMESPACE_URL, f"comment:{c.get('id', '')}"),
        ticket_id=ticket_uuid,
        author=(c.get("author") or {}).get("displayName") or "unknown",
        content=(text.strip() or "<empty>"),
    )


def _build_jql(
    project_key: str,
    status: TicketStatus | None,
    assignee: str | None,
    reporter: str | None,
) -> str:
    clauses: list[str] = [f'project = "{project_key}"']
    if status:
        name = {
            TicketStatus.OPEN: "Open",
            TicketStatus.IN_PROGRESS: "In Progress",
            TicketStatus.RESOLVED: "Done",
            TicketStatus.CLOSED: "Closed",
        }[status]
        clauses.append(f'status = "{name}"')
    if assignee:
        clauses.append(f'assignee in (currentUser(), "{assignee}")')
    if reporter:
        clauses.append(f'reporter = "{reporter}"')
    # Jira Cloud disallows unbounded JQL; always include a recent window to keep queries bounded.
    clauses.append("updated >= -365d")
    return " AND ".join(clauses) + " ORDER BY updated DESC"


async def _normalize_search_issue(user_id: str, entry: object) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        logger.warning("Skipping non-dict issue from Jira search: %r", entry)
        return None
    issue_key = entry.get("key")
    fields = entry.get("fields")
    if issue_key and isinstance(fields, dict):
        return entry
    issue_id = entry.get("id")
    if not issue_id:
        logger.warning("Skipping issue missing key/id in search response: %s", entry)
        return None
    try:
        hydrated = await jc.get_issue(user_id, issue_id)
    except (httpx.HTTPError, ValueError, TypeError, KeyError) as exc:
        logger.warning("Failed to hydrate issue %s: %s", issue_id, exc)
        return None
    issue_key = hydrated.get("key")
    fields = hydrated.get("fields")
    if not issue_key or not isinstance(fields, dict):
        logger.warning("Skipping issue missing key/fields after hydration: %s", hydrated)
        return None
    return hydrated


def _unique_issues_by_key(issues: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    seen: set[str] = set()
    unique: list[tuple[str, dict[str, Any]]] = []
    for issue in issues:
        key = issue.get("key")
        if not isinstance(key, str) or not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        unique.append((key, issue))
    return unique


def _status_targets(status: TicketStatus) -> list[str]:
    return {
        TicketStatus.OPEN: ["Open", "To Do"],
        TicketStatus.IN_PROGRESS: ["In Progress", "Doing"],
        TicketStatus.RESOLVED: ["Done", "Resolved"],
        TicketStatus.CLOSED: ["Closed", "Done", "Resolved"],
    }[status]


async def _transition_status(user_id: str, issue_key: str, status: TicketStatus) -> None:
    transitions = await jc.list_transitions(user_id, issue_key)
    targets = _status_targets(status)
    choice = next((t for name in targets for t in transitions if t.get("name") == name), None)
    if not choice:
        msg = f"No valid transition found to {status} for {issue_key}"
        raise ServiceError(msg)
    await jc.do_transition(user_id, issue_key, choice["id"])


async def _build_update_fields(
    user_id: str,
    title: str | None,
    description: str | None,
    priority: TicketPriority | None,
    assignee: str | None,
) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    if title is not None:
        fields["summary"] = title
    if description is not None:
        fields["description"] = description
    if priority is not None:
        fields["priority"] = {"name": _priority_to_jira(priority)}
    if assignee is not None:
        acct = await jc.find_user_account_id(user_id, assignee)
        if not acct:
            msg = f"Assignee '{assignee}' was not found"
            raise ServiceError(msg)
        fields["assignee"] = {"id": acct}
    return fields


# ---- concrete implementation ----


class TicketImpl(TicketServiceAPI):
    """Jira-backed implementation of the TicketServiceAPI.

    All methods are async and map domain UUIDs to Jira issue keys internally.
    """

    def __init__(self, user_id: str, project_key: str) -> None:
        """Initialize with a Jira-authorized user and a default project key."""
        self.user_id = user_id
        self.project_key = project_key

    # CREATE
    async def create_ticket(
        self,
        title: str,
        description: str,
        reporter: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        assignee: str | None = None,
    ) -> Ticket:
        """Create a ticket and return its hydrated domain model."""
        try:
            reporter_id = await jc.find_user_account_id(self.user_id, reporter) if reporter else None
            assignee_id = await jc.find_user_account_id(self.user_id, assignee) if assignee else None

            created = await jc.create_issue(
                user_id=self.user_id,
                project_key=self.project_key,
                summary=title,
                description=description,
                assignee_account_id=assignee_id,
                reporter_account_id=reporter_id,
            )

            key = created["key"]
            # update priority if needed
            if priority != TicketPriority.MEDIUM:
                await jc.update_issue_fields(self.user_id, key, {"priority": {"name": _priority_to_jira(priority)}})

            data = await jc.get_issue(self.user_id, key)
            return _jira_to_ticket(data, self.user_id)
        except Exception as e:
            msg = f"Failed to create ticket: {e}"
            raise ServiceError(msg) from e

    # READ ONE
    async def get_ticket(self, ticket_id: UUID) -> Ticket:
        """Get a single ticket by domain UUID; raise if not found."""
        key = get_key_for_uuid(self.user_id, ticket_id) or str(ticket_id)
        try:
            data = await jc.get_issue(self.user_id, key)
        except Exception as e:
            raise TicketNotFoundError(ticket_id) from e
        return _jira_to_ticket(data, self.user_id)

    # LIST (with basic filters → JQL)
    async def list_tickets(
        self,
        status: TicketStatus | None = None,
        assignee: str | None = None,
        reporter: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Ticket]:
        """List tickets with simple filters using JQL."""
        if limit < 0 or offset < 0:
            msg = "limit/offset must be non-negative."
            raise ValueError(msg)

        jql = _build_jql(self.project_key, status, assignee, reporter)
        try:
            raw = await jc.search_issues(self.user_id, jql=jql, max_results=min(50, limit), start_at=offset)
            logger.debug("Jira search raw response: %s", raw)
        except Exception as e:
            msg = f"Failed to list tickets: {e}"
            raise ServiceError(msg) from e

        # The /search/jql endpoint returns issues directly in the response
        issues = raw.get("issues", [])
        if not isinstance(issues, list):
            msg = "Unexpected Jira search response: issues is not a list."
            raise ServiceError(msg)
        logger.info("Jira search returned %d issues", len(issues))

        hydrated: list[dict[str, Any]] = []
        for entry in issues:
            issue = await _normalize_search_issue(self.user_id, entry)
            if issue:
                hydrated.append(issue)

        unique_issues = _unique_issues_by_key(hydrated)
        tickets: list[Ticket] = []
        pairs: list[tuple[UUID, str]] = []
        for issue_key, issue in unique_issues:
            ticket = _jira_to_ticket(issue, self.user_id)
            tickets.append(ticket)
            pairs.append((ticket.id, issue_key))
        if pairs:
            ensure_mapping_for_keys(self.user_id, pairs)
        return tickets

    # UPDATE
    async def update_ticket(  # noqa: PLR0913 - API requires multiple optional params
        self,
        ticket_id: UUID,
        title: str | None = None,
        description: str | None = None,
        status: TicketStatus | None = None,
        priority: TicketPriority | None = None,
        assignee: str | None = None,
    ) -> Ticket:
        """Update fields and/or workflow state; return the refreshed ticket."""
        key = get_key_for_uuid(self.user_id, ticket_id) or str(ticket_id)
        try:
            if status:
                await _transition_status(self.user_id, key, status)
            fields = await _build_update_fields(self.user_id, title, description, priority, assignee)
            if fields:
                await jc.update_issue_fields(self.user_id, key, fields)
            data = await jc.get_issue(self.user_id, key)
            return _jira_to_ticket(data, self.user_id)
        except TicketNotFoundError:
            raise
        except Exception as e:
            msg = f"Failed to update ticket: {e}"
            raise ServiceError(msg) from e

    async def reassign_ticket(self, ticket_id: UUID, new_assignee: str) -> Ticket:
        """Reassign the ticket to a new assignee and return the updated ticket."""
        key = get_key_for_uuid(self.user_id, ticket_id) or str(ticket_id)
        try:
            acct = await jc.find_user_account_id(self.user_id, new_assignee)
            if not acct:
                msg = f"Assignee '{new_assignee}' was not found"
                raise ServiceError(msg)
            await jc.update_issue_fields(self.user_id, key, {"assignee": {"id": acct}})
            data = await jc.get_issue(self.user_id, key)
            return _jira_to_ticket(data, self.user_id)
        except TicketNotFoundError:
            raise
        except Exception as e:
            msg = f"Failed to reassign ticket: {e}"
            raise ServiceError(msg) from e

    async def update_priority(self, ticket_id: UUID, new_priority: TicketPriority) -> Ticket:
        """Update the ticket priority and return the updated ticket."""
        key = get_key_for_uuid(self.user_id, ticket_id) or str(ticket_id)
        try:
            await jc.update_issue_fields(self.user_id, key, {"priority": {"name": _priority_to_jira(new_priority)}})
            data = await jc.get_issue(self.user_id, key)
            return _jira_to_ticket(data, self.user_id)
        except TicketNotFoundError:
            raise
        except Exception as e:
            msg = f"Failed to update priority: {e}"
            raise ServiceError(msg) from e

    async def update_description(self, ticket_id: UUID, new_description: str) -> Ticket:
        """Update the ticket description and return the updated ticket."""
        key = get_key_for_uuid(self.user_id, ticket_id) or str(ticket_id)
        try:
            await jc.update_issue_fields(self.user_id, key, {"description": new_description})
            data = await jc.get_issue(self.user_id, key)
        except Exception as e:
            raise TicketNotFoundError(ticket_id) from e

        return _jira_to_ticket(data, self.user_id)

    # DELETE
    async def delete_ticket(self, ticket_id: UUID) -> bool:
        """Delete a ticket by UUID mapped to a Jira issue key."""
        key = get_key_for_uuid(self.user_id, ticket_id) or str(ticket_id)
        try:
            return await jc.delete_issue(self.user_id, key)
        except Exception as e:
            msg = f"Failed to delete ticket: {e}"
            raise ServiceError(msg) from e

    # COMMENTS
    async def add_comment(self, ticket_id: UUID, author: str, content: str) -> Comment:  # noqa: ARG002
        """Add a comment and return it in domain form.

        Note: The author parameter is not used because Jira automatically assigns
        comments to the authenticated user making the API call.
        """
        key = get_key_for_uuid(self.user_id, ticket_id) or str(ticket_id)
        try:
            data = await jc.add_comment(self.user_id, key, content)
        except Exception as e:
            raise TicketNotFoundError(ticket_id) from e

        return _jira_comment_to_domain(data, ticket_id)

    async def get_ticket_comments(self, ticket_id: UUID) -> list[Comment]:
        """Return all comments for a ticket as domain objects."""
        key = get_key_for_uuid(self.user_id, ticket_id) or str(ticket_id)
        raw = await jc.get_comments(self.user_id, key)
        comments = raw.get("comments", [])
        return [_jira_comment_to_domain(c, ticket_id) for c in comments]

    async def transition_status(self, ticket_id: UUID, new_status: TicketStatus) -> Ticket:
        """Transition the ticket to a new status and return the updated ticket."""
        return await self.update_ticket(ticket_id, status=new_status)
