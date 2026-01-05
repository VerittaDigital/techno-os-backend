/**
 * ERROR HANDLING MODULE
 * 
 * Implements fail-closed error handling per ERROR_POLICY.md
 * All errors are normalized to StatusType (APPROVED|BLOCKED|EXPIRED|WARNING|NEUTRAL)
 * 
 * Framework: F-CONSOLE-0.1 Etapa 4
 * Status: Production-ready
 */

export type StatusType = 'APPROVED' | 'BLOCKED' | 'EXPIRED' | 'WARNING' | 'NEUTRAL';

export interface ApiResponse<T = any> {
  status: StatusType;
  ts_utc: string;
  trace_id: string;
  reason_codes?: string[];
  data?: T;
  message?: string;
  httpStatus?: number;
}

export interface ExecuteResponse {
  status: StatusType;
  ts_utc: string;
  trace_id: string;
  reason_codes?: string[];
}

export interface ErrorContext {
  endpoint: string;
  method: string;
  httpStatus?: number;
  error?: Error | string;
  responseData?: any;
  timeout?: boolean;
  networkError?: boolean;
}

/**
 * FAIL-CLOSED ERROR HANDLER
 * 
 * When in doubt, return BLOCKED
 */
class ErrorHandler {
  /**
   * Normalize any error to BLOCKED status
   * Never throw; always return a valid ApiResponse
   */
  static normalize(context: ErrorContext): ApiResponse {
    const timestamp = new Date().toISOString();
    
    // Network error (timeout > 15s)
    if (context.timeout) {
      return {
        status: 'BLOCKED',
        ts_utc: timestamp,
        trace_id: `${context.endpoint}-timeout`,
        reason_codes: ['TIMEOUT_EXCEEDED'],
        message: 'Request timeout (>15s)',
        httpStatus: 0,
      };
    }

    // Network error (unreachable backend)
    if (context.networkError) {
      return {
        status: 'BLOCKED',
        ts_utc: timestamp,
        trace_id: `${context.endpoint}-network-error`,
        reason_codes: ['NETWORK_UNREACHABLE'],
        message: 'Backend unreachable',
        httpStatus: 0,
      };
    }

    // HTTP 401/403 — Authentication failed
    if (context.httpStatus === 401 || context.httpStatus === 403) {
      return {
        status: 'BLOCKED',
        ts_utc: timestamp,
        trace_id: `${context.endpoint}-auth-failed`,
        reason_codes: ['API_KEY_INVALID'],
        message: 'Autenticacao falhou',
        httpStatus: context.httpStatus,
      };
    }

    // HTTP 400 — Malformed request
    if (context.httpStatus === 400) {
      return {
        status: 'BLOCKED',
        ts_utc: timestamp,
        trace_id: `${context.endpoint}-bad-request`,
        reason_codes: ['VALIDATION_FAILED'],
        message: 'Invalid request format',
        httpStatus: 400,
      };
    }

    // HTTP 5XX — Server error
    if (context.httpStatus && context.httpStatus >= 500) {
      return {
        status: 'BLOCKED',
        ts_utc: timestamp,
        trace_id: `${context.endpoint}-server-error`,
        reason_codes: ['SERVER_ERROR'],
        message: 'Server error',
        httpStatus: context.httpStatus,
      };
    }

    // Malformed response body (missing required fields)
    if (context.responseData && !this.isValidResponse(context.responseData)) {
      return {
        status: 'BLOCKED',
        ts_utc: timestamp,
        trace_id: `${context.endpoint}-malformed-response`,
        reason_codes: ['MALFORMED_RESPONSE'],
        message: 'Backend returned invalid response',
        httpStatus: 200, // Backend sent HTTP 200 but response was invalid
      };
    }

    // Unknown status value → normalize to BLOCKED
    if (context.responseData?.status && !this.isValidStatus(context.responseData.status)) {
      return {
        status: 'BLOCKED',
        ts_utc: timestamp,
        trace_id: context.responseData.trace_id || `${context.endpoint}-unknown-status`,
        reason_codes: ['UNKNOWN_STATUS'],
        message: `Unknown status: ${context.responseData.status}`,
        httpStatus: 200,
      };
    }

    // Generic error fallback
    return {
      status: 'BLOCKED',
      ts_utc: timestamp,
      trace_id: `${context.endpoint}-unknown-error`,
      reason_codes: ['UNKNOWN_ERROR'],
      message: typeof context.error === 'string' ? context.error : 'Unknown error',
      httpStatus: context.httpStatus || 0,
    };
  }

  /**
   * Check if response has all required fields
   */
  private static isValidResponse(data: any): boolean {
    return (
      data &&
      typeof data === 'object' &&
      'status' in data &&
      'ts_utc' in data &&
      'trace_id' in data &&
      typeof data.status === 'string' &&
      typeof data.ts_utc === 'string' &&
      typeof data.trace_id === 'string'
    );
  }

  /**
   * Check if status is a valid StatusType
   */
  private static isValidStatus(status: string): boolean {
    return ['APPROVED', 'BLOCKED', 'EXPIRED', 'WARNING', 'NEUTRAL'].includes(status);
  }
}

/**
 * TIMEOUT HANDLER
 * 
 * AbortController hardcoded to 15 seconds (per CONTRACT.md)
 */
export function createTimeoutController(timeoutMs: number = 15000): AbortController {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  // Store for cleanup
  (controller as any)._timeoutId = timeoutId;
  
  return controller;
}

/**
 * CLEANUP TIMEOUT
 */
export function clearTimeoutController(controller: AbortController): void {
  const timeoutId = (controller as any)._timeoutId;
  if (timeoutId) {
    clearTimeout(timeoutId);
  }
}

/**
 * FETCH WRAPPER WITH FAIL-CLOSED BEHAVIOR
 */
export async function fetchWithTimeout(
  url: string,
  options: RequestInit & { timeout?: number } = {}
): Promise<ApiResponse> {
  const { timeout = 15000, ...fetchOptions } = options;
  const controller = createTimeoutController(timeout);
  
  const endpoint = new URL(url, typeof window !== 'undefined' ? window.location.origin : '').pathname;
  const method = fetchOptions.method || 'GET';

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    });

    const data = await response.json();

    // HTTP 200 but status might be BLOCKED
    if (response.ok) {
      if (ErrorHandler.isValidResponse(data)) {
        // Return as-is (may contain BLOCKED status)
        return data as ApiResponse;
      } else {
        // Invalid response structure
        return ErrorHandler.normalize({
          endpoint,
          method,
          httpStatus: 200,
          responseData: data,
        });
      }
    } else {
      // HTTP error (4XX, 5XX)
      return ErrorHandler.normalize({
        endpoint,
        method,
        httpStatus: response.status,
        responseData: data,
      });
    }
  } catch (error) {
    // Timeout or network error
    const isTimeout = error instanceof DOMException && error.name === 'AbortError';
    const isNetwork = error instanceof TypeError;

    return ErrorHandler.normalize({
      endpoint,
      method,
      error: String(error),
      timeout: isTimeout,
      networkError: isNetwork && !isTimeout,
    });
  } finally {
    clearTimeoutController(controller);
  }
}

/**
 * EXECUTE COMMAND WITH FAIL-CLOSED BEHAVIOR
 */
export async function executeCommand(
  command: string,
  sessionId?: string
): Promise<ExecuteResponse> {
  if (!command || !/^[A-Z_]+$/.test(command)) {
    return ErrorHandler.normalize({
      endpoint: '/api/execute',
      method: 'POST',
      error: 'Invalid command format (must be uppercase + underscore)',
    }) as ExecuteResponse;
  }

  const response = await fetchWithTimeout('/api/execute', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || '',
    },
    body: JSON.stringify({ command, session_id: sessionId }),
  });

  return {
    status: response.status,
    ts_utc: response.ts_utc,
    trace_id: response.trace_id,
    reason_codes: response.reason_codes,
  };
}

/**
 * FETCH AUDIT LOG WITH FALLBACK
 */
export async function fetchAuditLog(
  filter: string = 'all',
  limit: number = 50
): Promise<any[]> {
  // Try primary endpoint
  const response = await fetchWithTimeout('/api/audit', {
    method: 'GET',
    headers: {
      'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || '',
    },
  });

  // If BLOCKED, try fallback
  if (response.status === 'BLOCKED') {
    const fallback = await fetchWithTimeout('/api/diagnostic/metrics', {
      method: 'GET',
      headers: {
        'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || '',
      },
    });

    if (fallback.status === 'BLOCKED') {
      // Both failed; return empty array (fail-closed)
      return [];
    }

    return fallback.data || [];
  }

  return response.data || [];
}

/**
 * FETCH MEMORY SNAPSHOT WITH NULL HANDLING
 */
export async function fetchMemory(): Promise<any | null> {
  const response = await fetchWithTimeout('/api/memory', {
    method: 'GET',
    headers: {
      'X-API-Key': process.env.NEXT_PUBLIC_API_KEY || '',
    },
  });

  // If BLOCKED or no data, return null (fail-closed)
  if (response.status === 'BLOCKED' || !response.data) {
    return null;
  }

  return response.data;
}

/**
 * VALIDATE STATUS ENUM
 */
export function validateStatus(status: unknown): StatusType {
  if (typeof status === 'string' && ['APPROVED', 'BLOCKED', 'EXPIRED', 'WARNING', 'NEUTRAL'].includes(status)) {
    return status as StatusType;
  }
  // Unknown status → normalize to BLOCKED (fail-closed)
  return 'BLOCKED';
}

/**
 * EXPORT ERROR HANDLER FOR DIRECT USE
 */
export const errorHandler = ErrorHandler;

export default ErrorHandler;
