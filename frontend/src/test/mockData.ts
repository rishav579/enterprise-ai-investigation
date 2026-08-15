import type { FullInvestigationResponse, ScenarioItem } from '../api/types';

export const mockScenarioList: ScenarioItem[] = [
  {
    id: 'scenario_A_churn',
    name: 'Q3 Customer Churn Spike',
    question: 'Why did customer cancellations increase sharply in September 2025?',
    category: 'churn',
    expected_behavior: 'Identifies billing-gateway v2.4.0 bug.',
  },
  {
    id: 'scenario_D_insufficient',
    name: 'Insufficient Evidence Handling',
    question: 'Investigate why the unicorn delivery fleet routing algorithm failed on Mars.',
    category: 'insufficient_evidence',
    expected_behavior: 'Gracefully concludes INSUFFICIENT_EVIDENCE.',
  },
];

export const mockFullInvestigationResponse: FullInvestigationResponse = {
  run_result: {
    investigation_id: 'INV-TEST-001',
    question: 'Why did customer cancellations increase sharply in September 2025?',
    status: 'completed',
    plan: {
      plan_id: 'PLAN-TEST-001',
      investigation_id: 'INV-TEST-001',
      question: 'Why did customer cancellations increase sharply in September 2025?',
      scenario: 'churn_spike_investigation',
      total_steps: 2,
      steps: [
        {
          step_id: 'STEP-01',
          objective: 'Establish monthly cancellation baseline',
          rationale: 'Verify whether an anomaly exists in September 2025.',
          tool_name: 'sql_investigation',
          tool_input: {
            query: 'SELECT strftime("%Y-%m", cancellation_date) AS churn_month, COUNT(*) AS total_cancellations FROM subscriptions GROUP BY churn_month',
          },
          expected_evidence_type: 'time_series_cancellations',
          depends_on: [],
        },
        {
          step_id: 'STEP-02',
          objective: 'Retrieve postmortem for billing gateway incident',
          rationale: 'Confirm root cause of failed transactions.',
          tool_name: 'document_retrieval',
          tool_input: {
            action: 'get',
            path: 'postmortem_inc_2025_002.md',
          },
          expected_evidence_type: 'document_text',
          depends_on: ['STEP-01'],
        },
      ],
    },
    step_results: [
      {
        step_id: 'STEP-01',
        status: 'completed',
        tool_name: 'sql_investigation',
        tool_input: {
          query: 'SELECT strftime("%Y-%m", cancellation_date) AS churn_month, COUNT(*) AS total_cancellations FROM subscriptions GROUP BY churn_month',
        },
        tool_output: {
          columns: ['churn_month', 'total_cancellations'],
          rows: [
            { churn_month: '2025-08', total_cancellations: 12 },
            { churn_month: '2025-09', total_cancellations: 148 },
          ],
          row_count: 2,
        },
        row_count: 2,
        evidence_summary: 'SQL query returned 2 row(s).',
        evidence_ids: ['EVID-001'],
      },
      {
        step_id: 'STEP-02',
        status: 'completed',
        tool_name: 'document_retrieval',
        tool_input: {
          action: 'get',
          path: 'postmortem_inc_2025_002.md',
        },
        tool_output: {
          document_id: 'postmortem_inc_2025_002.md',
          full_text: 'Incident Postmortem: billing-gateway v2.4.0 introduced webhook confirmation bug.',
          char_count: 81,
        },
        evidence_summary: 'Retrieved document postmortem_inc_2025_002.md.',
        evidence_ids: ['EVID-002'],
      },
    ],
    total_steps: 2,
    completed_steps: 2,
    failed_steps: 0,
    skipped_steps: 0,
    total_evidence_items: 2,
    audit_event_count: 5,
  },
  report: {
    investigation_run_id: 'INV-TEST-001',
    question: 'Why did customer cancellations increase sharply in September 2025?',
    executive_summary:
      'Customer cancellations surged 12x in September 2025 due to a webhook parsing bug in billing-gateway v2.4.0 release.',
    root_cause:
      'Deployment of billing-gateway v2.4.0 introduced a webhook parsing regression that erroneously marked legitimate customer transactions as failed.',
    findings: [
      {
        finding_id: 'FND-001',
        statement:
          'Customer cancellations spiked significantly in September 2025 reaching 148 cancellations.',
        evidence_ids: ['EVID-001'],
        confidence: 'high',
      },
      {
        finding_id: 'FND-002',
        statement:
          'Internal postmortem INC-2025-002 confirms webhook confirmation logic bug in v2.4.0.',
        evidence_ids: ['EVID-002'],
        confidence: 'high',
      },
    ],
    contributing_factors: [
      'Support queue backlog delayed customer ticket turnaround.',
    ],
    recommendations: [
      {
        recommendation_id: 'REC-001',
        action:
          'Implement end-to-end webhook integration test suites for billing-gateway.',
        rationale:
          'Prevent unhandled webhook response schema regressions from causing automated account lockouts.',
        evidence_ids: ['EVID-002'],
        priority: 'critical',
      },
    ],
    limitations: [
      'Analysis restricted to data available in relational telemetry up to Q3 2025.',
    ],
    evidence_ids: ['EVID-001', 'EVID-002'],
    citation_valid: true,
    synthesis_status: 'success',
    validation_errors: [],
  },
  evidence_items: [
    {
      evidence_id: 'EVID-001',
      investigation_run_id: 'INV-TEST-001',
      step_id: 'STEP-01',
      tool_name: 'sql_investigation',
      evidence_type: 'sql_result',
      source_reference: 'sql_investigation:STEP-01',
      content: {
        query_reference: 'SELECT strftime("%Y-%m", cancellation_date) AS churn_month, COUNT(*) AS total_cancellations FROM subscriptions GROUP BY churn_month',
        columns: ['churn_month', 'total_cancellations'],
        rows: [
          { churn_month: '2025-08', total_cancellations: 12 },
          { churn_month: '2025-09', total_cancellations: 148 },
        ],
        row_count: 2,
        truncated: false,
      },
      content_hash: 'a3f89e2c45d6108b3c99f1234567890abcdef1234567890abcdef1234567890a',
      sequence_number: 1,
    },
    {
      evidence_id: 'EVID-002',
      investigation_run_id: 'INV-TEST-001',
      step_id: 'STEP-02',
      tool_name: 'document_retrieval',
      evidence_type: 'document_text',
      source_reference: 'document_retrieval:postmortem_inc_2025_002.md',
      content: {
        document_id: 'postmortem_inc_2025_002.md',
        full_text: 'Incident Postmortem: billing-gateway v2.4.0 introduced webhook confirmation bug.',
        char_count: 81,
      },
      content_hash: 'b4e76d1a90c5234f5e88a0987654321fedcba0987654321fedcba0987654321b',
      sequence_number: 2,
    },
  ],
  audit_events: [
    {
      event_id: 'AUDIT-001',
      investigation_run_id: 'INV-TEST-001',
      event_type: 'investigation_started',
      sequence_number: 1,
      evidence_ids: [],
      metadata: { question: 'Why did customer cancellations increase?' },
    },
    {
      event_id: 'AUDIT-002',
      investigation_run_id: 'INV-TEST-001',
      event_type: 'plan_created',
      sequence_number: 2,
      evidence_ids: [],
      metadata: { total_steps: 2 },
    },
    {
      event_id: 'AUDIT-003',
      investigation_run_id: 'INV-TEST-001',
      event_type: 'step_started',
      step_id: 'STEP-01',
      tool_name: 'sql_investigation',
      sequence_number: 3,
      evidence_ids: [],
    },
    {
      event_id: 'AUDIT-004',
      investigation_run_id: 'INV-TEST-001',
      event_type: 'evidence_collected',
      step_id: 'STEP-01',
      tool_name: 'sql_investigation',
      sequence_number: 4,
      evidence_ids: ['EVID-001'],
      metadata: { evidence_count: 1 },
    },
    {
      event_id: 'AUDIT-005',
      investigation_run_id: 'INV-TEST-001',
      event_type: 'synthesis_validated',
      sequence_number: 5,
      evidence_ids: ['EVID-001', 'EVID-002'],
      metadata: { citation_valid: true },
    },
  ],
};
