export type ExecutionStatus = "pending" | "running" | "completed" | "failed";

export type TestResultStatus =
  | "passed"
  | "failed"
  | "time_limit_exceeded"
  | "memory_limit_exceeded"
  | "compilation_error"
  | "runtime_error";

export interface TestResultPublic {
  id: string;
  test_case_id: string;
  status: TestResultStatus;
  is_hidden: boolean;
  input_data?: string | null;
  expected_output?: string | null;
  actual_output?: string | null;
  execution_time_ms?: number | null;
  memory_kb?: number | null;
  error_category?: string | null;
  created_at: string;
}

export interface CodingSubmissionPublic {
  id: string;
  session_id: string;
  question_id: string;
  user_id: string;
  language_id: number;
  source_code: string;
  execution_status: ExecutionStatus;
  passed_tests: number;
  total_tests: number;
  runtime_ms?: number | null;
  memory_kb?: number | null;
  submitted_at: string;
}

export interface CodingSubmissionCreate {
  question_id: string;
  language_id?: number;
  source_code: string;
  idempotency_key?: string;
}
