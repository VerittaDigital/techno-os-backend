"""Gate F2.3 (Bearer Token + Session) with DB persistence."""

from typing import Optional
import hashlib
from sqlalchemy.orm import Session

from app.decision_record import DecisionRecord
from app.db.session_repository import SessionRepository


class GateF23SessionDB:
    """
    F2.3 Bearer Token Gate with Database Persistence
    
    Validates:
    1. Bearer token format (session_id)
    2. User-ID header (user_id)
    3. Session existence + validity in DB
    4. Session binding (user_id + api_key_hash)
    
    Fail-closed: Any validation failure → DENY
    """
    
    PROFILE_ID = "F2.3"
    
    def __init__(self, db: Session):
        self.db = db
        self.repo = SessionRepository(db)
    
    def evaluate(
        self,
        authorization_header: Optional[str],
        user_id_header: Optional[str],
        api_key_hash: str,
        trace_id: str,
        input_payload: dict = None,
    ) -> DecisionRecord:
        """
        Evaluate F2.3 Bearer Token gate with DB session lookup.
        
        Args:
            authorization_header: "Bearer <session_id>"
            user_id_header: "X-VERITTA-USER-ID" value
            api_key_hash: SHA256 of API key (from F2.1)
            trace_id: Trace ID for correlation
            input_payload: Optional input for digest computation
        
        Returns:
            DecisionRecord (ALLOW or DENY)
        """
        
        # Step 1: Check authorization header
        if not authorization_header:
            return DecisionRecord(
                decision="DENY",
                profile_id=self.PROFILE_ID,
                reason_codes=["F2_3_MISSING_AUTHORIZATION"],
                matched_rules=["Authorization header missing"],
                input_payload=input_payload,
                trace_id=trace_id,
            )
        
        # Step 2: Parse Bearer token
        session_id = self._parse_bearer_token(authorization_header)
        if not session_id:
            return DecisionRecord(
                decision="DENY",
                profile_id=self.PROFILE_ID,
                reason_codes=["F2_3_INVALID_BEARER_FORMAT"],
                matched_rules=["Bearer token format invalid"],
                input_payload=input_payload,
                trace_id=trace_id,
            )
        
        # Step 3: Check user-id header
        if not user_id_header:
            return DecisionRecord(
                decision="DENY",
                profile_id=self.PROFILE_ID,
                reason_codes=["F2_3_MISSING_USER_ID"],
                matched_rules=["X-VERITTA-USER-ID header missing"],
                input_payload=input_payload,
                trace_id=trace_id,
            )
        
        # Step 4: Validate session from DB
        is_valid, reason_code = self.repo.validate(session_id)
        
        if not is_valid:
            return DecisionRecord(
                decision="DENY",
                profile_id=self.PROFILE_ID,
                reason_codes=[reason_code],  # SESSION_INVALID, SESSION_EXPIRED, SESSION_REVOKED
                matched_rules=[f"Session validation failed: {reason_code}"],
                input_payload=input_payload,
                trace_id=trace_id,
            )
        
        # Step 5: Verify session binding (user_id + api_key_hash)
        session = self.repo.get_by_id(session_id)
        if not session:
            return DecisionRecord(
                decision="DENY",
                profile_id=self.PROFILE_ID,
                reason_codes=["F2_3_SESSION_NOT_FOUND"],
                matched_rules=["Session not found in database"],
                input_payload=input_payload,
                trace_id=trace_id,
            )
        
        if session.user_id != user_id_header:
            return DecisionRecord(
                decision="DENY",
                profile_id=self.PROFILE_ID,
                reason_codes=["F2_3_USER_MISMATCH"],
                matched_rules=["User-ID header does not match session user_id"],
                input_payload=input_payload,
                trace_id=trace_id,
            )
        
        if session.api_key_hash != api_key_hash:
            return DecisionRecord(
                decision="DENY",
                profile_id=self.PROFILE_ID,
                reason_codes=["F2_3_API_KEY_MISMATCH"],
                matched_rules=["API key hash does not match session binding"],
                input_payload=input_payload,
                trace_id=trace_id,
            )
        
        # All checks passed
        return DecisionRecord(
            decision="ALLOW",
            profile_id=self.PROFILE_ID,
            reason_codes=[],
            matched_rules=[
                "Bearer token valid",
                "User-ID bound to session",
                "API key binding verified",
                "Session not expired",
                "Session not revoked",
            ],
            input_payload=input_payload,
            trace_id=trace_id,
        )
    
    def create_session(
        self,
        user_id: str,
        api_key_hash: str,
        ttl_hours: int = 8,
    ) -> str:
        """
        Create a new F2.3 session.
        
        Returns:
            session_id (to be returned as Bearer token)
        """
        session = self.repo.create(
            user_id=user_id,
            api_key_hash=api_key_hash,
            ttl_hours=ttl_hours,
        )
        return session.session_id
    
    def revoke_session(self, session_id: str) -> bool:
        """
        Revoke a session (admin operation).
        
        Returns:
            True if revoked, False if not found
        """
        result = self.repo.revoke(session_id)
        return result is not None
    
    @staticmethod
    def _parse_bearer_token(auth_header: str) -> Optional[str]:
        """
        Parse Bearer token from Authorization header.
        
        Format: "Bearer <session_id>"
        Returns:
            session_id if valid format, None otherwise
        """
        if not auth_header:
            return None
        
        parts = auth_header.split()
        if len(parts) != 2:
            return None
        
        scheme, token = parts
        if scheme.lower() != "bearer":
            return None
        
        # Basic format check: UUID v4 = 36 chars
        if len(token) != 36:
            return None
        
        return token
