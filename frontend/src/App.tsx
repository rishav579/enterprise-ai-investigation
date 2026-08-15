import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { QuestionInput } from './components/QuestionInput';
import { InvestigationTimeline } from './components/InvestigationTimeline';
import { FindingsSection } from './components/FindingsSection';
import { RecommendationsSection } from './components/RecommendationsSection';
import { EvidenceInspector } from './components/EvidenceInspector';
import { AuditTrailStream } from './components/AuditTrailStream';
import { GuardrailsBanner } from './components/GuardrailsBanner';
import { ErrorBanner } from './components/ErrorBanner';
import { EmptyState } from './components/EmptyState';
import { apiClient } from './api/client';
import type {
  BackendHealthResponse,
  EvidenceItem,
  FullInvestigationResponse,
  ScenarioItem,
} from './api/types';
import {
  FileText,
  Clock,
  History,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

const DEFAULT_QUESTION = 'Why did customer cancellations increase sharply in September 2025?';

export const App: React.FC = () => {
  const [health, setHealth] = useState<BackendHealthResponse | null>(null);
  const [healthLoading, setHealthLoading] = useState<boolean>(true);
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario_A_churn');
  const [question, setQuestion] = useState<string>(DEFAULT_QUESTION);
  const [investigationData, setInvestigationData] = useState<FullInvestigationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'audit'>('overview');

  // Check health on load
  const fetchHealthStatus = useCallback(async () => {
    setHealthLoading(true);
    try {
      const data = await apiClient.checkHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    } finally {
      setHealthLoading(false);
    }
  }, []);

  // Fetch preset scenarios on load
  const fetchScenarios = useCallback(async () => {
    try {
      const items = await apiClient.fetchScenarios();
      setScenarios(items);
    } catch {
      // Fallback default scenarios if offline
      setScenarios([
        {
          id: 'scenario_A_churn',
          name: 'Q3 Customer Churn Spike',
          question: DEFAULT_QUESTION,
          category: 'churn',
          expected_behavior: 'Identifies billing-gateway v2.4.0 bug.',
        },
      ]);
    }
  }, []);

  useEffect(() => {
    fetchHealthStatus();
    fetchScenarios();
  }, [fetchHealthStatus, fetchScenarios]);

  // Handle Scenario selection
  const handleSelectScenario = (scenario: ScenarioItem) => {
    setSelectedScenarioId(scenario.id);
    setQuestion(scenario.question);
  };

  // Run Investigation execution
  const handleRunInvestigation = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.runInvestigation({
        question,
        scenario_hint: selectedScenarioId ? selectedScenarioId.replace('scenario_', '') : undefined,
      });
      setInvestigationData(response);
      setActiveTab('overview');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Investigation failed unexpectedly.';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setQuestion('');
    setSelectedScenarioId('');
    setInvestigationData(null);
    setError(null);
    setSelectedEvidenceId(null);
  };

  // Find currently selected EvidenceItem from data
  const activeEvidenceItem: EvidenceItem | null =
    investigationData && selectedEvidenceId
      ? investigationData.evidence_items.find((item) => item.evidence_id === selectedEvidenceId) || null
      : null;

  const isBackendOnline = health?.status === 'ok';

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--bg-app)' }}>
      {/* Top Operations Header */}
      <Header
        health={health}
        healthLoading={healthLoading}
        onRefreshHealth={fetchHealthStatus}
        investigationId={investigationData?.run_result.investigation_id}
      />

      {/* Main Workspace Layout */}
      <main style={{
        maxWidth: '1240px',
        width: '100%',
        margin: '0 auto',
        padding: '24px 20px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        flex: 1,
      }}>
        {/* Guardrails Banner */}
        <GuardrailsBanner />

        {/* Question & Scenario Dispatch Card */}
        <QuestionInput
          question={question}
          onChangeQuestion={setQuestion}
          onRunInvestigation={handleRunInvestigation}
          onReset={handleReset}
          isLoading={isLoading}
          scenarios={scenarios}
          selectedScenarioId={selectedScenarioId}
          onSelectScenario={handleSelectScenario}
          isBackendOnline={isBackendOnline}
        />

        {/* Error Banner */}
        {error && <ErrorBanner error={error} onDismiss={() => setError(null)} onRetry={handleRunInvestigation} />}

        {/* Results Area */}
        {investigationData ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Run KPI Summary Bar */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '12px',
            }}>
              <div style={{
                backgroundColor: 'var(--bg-panel)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 16px',
              }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Investigation Status
                </div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'capitalize', display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                  {investigationData.run_result.status === 'completed' ? (
                    <CheckCircle2 size={16} color="var(--color-success)" />
                  ) : (
                    <AlertTriangle size={16} color="var(--color-warning)" />
                  )}
                  {investigationData.run_result.status}
                </div>
              </div>

              <div style={{
                backgroundColor: 'var(--bg-panel)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 16px',
              }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Planned Steps Executed
                </div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                  {investigationData.run_result.completed_steps} / {investigationData.run_result.total_steps} Completed
                </div>
              </div>

              <div style={{
                backgroundColor: 'var(--bg-panel)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 16px',
              }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Collected Evidence
                </div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-primary)', marginTop: '2px' }}>
                  {investigationData.evidence_items.length} Hashed Artifacts
                </div>
              </div>

              <div style={{
                backgroundColor: 'var(--bg-panel)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                padding: '12px 16px',
              }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                  Audit Trail
                </div>
                <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '2px' }}>
                  {investigationData.audit_events.length} Lifecycle Events
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div style={{
              display: 'flex',
              borderBottom: '1px solid var(--border-default)',
              gap: '12px',
            }}>
              <button
                type="button"
                onClick={() => setActiveTab('overview')}
                style={{
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === 'overview' ? '2px solid var(--color-primary)' : '2px solid transparent',
                  color: activeTab === 'overview' ? 'var(--color-primary)' : 'var(--text-secondary)',
                  padding: '10px 14px',
                  fontSize: '13px',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <FileText size={15} />
                Findings & Recommendations
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('timeline')}
                style={{
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === 'timeline' ? '2px solid var(--color-primary)' : '2px solid transparent',
                  color: activeTab === 'timeline' ? 'var(--color-primary)' : 'var(--text-secondary)',
                  padding: '10px 14px',
                  fontSize: '13px',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <Clock size={15} />
                Investigation Steps ({investigationData.run_result.plan.steps.length})
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('audit')}
                style={{
                  background: 'none',
                  border: 'none',
                  borderBottom: activeTab === 'audit' ? '2px solid var(--color-primary)' : '2px solid transparent',
                  color: activeTab === 'audit' ? 'var(--color-primary)' : 'var(--text-secondary)',
                  padding: '10px 14px',
                  fontSize: '13px',
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                }}
              >
                <History size={15} />
                Immutable Audit Trail ({investigationData.audit_events.length})
              </button>
            </div>

            {/* Active Tab View */}
            {activeTab === 'overview' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <FindingsSection
                  report={investigationData.report}
                  onSelectEvidenceId={setSelectedEvidenceId}
                />

                <RecommendationsSection
                  recommendations={investigationData.report.recommendations}
                  onSelectEvidenceId={setSelectedEvidenceId}
                />
              </div>
            )}

            {activeTab === 'timeline' && (
              <InvestigationTimeline
                plan={investigationData.run_result.plan}
                stepResults={investigationData.run_result.step_results}
                onSelectEvidenceId={setSelectedEvidenceId}
              />
            )}

            {activeTab === 'audit' && (
              <AuditTrailStream auditEvents={investigationData.audit_events} />
            )}
          </div>
        ) : !isLoading ? (
          <EmptyState
            scenarios={scenarios}
            onSelectScenario={(sc) => {
              handleSelectScenario(sc);
              setTimeout(() => handleRunInvestigation(), 50);
            }}
          />
        ) : null}

        {/* Evidence Inspector Drawer/Modal */}
        {selectedEvidenceId && (
          <EvidenceInspector
            evidenceItem={activeEvidenceItem}
            onClose={() => setSelectedEvidenceId(null)}
          />
        )}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-default)',
        backgroundColor: 'var(--bg-panel)',
        padding: '16px 24px',
        textAlign: 'center',
        fontSize: '12px',
        color: 'var(--text-muted)',
      }}>
        <div>
          Enterprise AI Investigation & Decision System &bull; Portfolio Simulation Project
        </div>
        <div style={{ marginTop: '4px', fontSize: '11px' }}>
          Zero-Fabrication Synthesis &bull; AST-Level Read-Only SQL &bull; SHA-256 Tamper-Evident Evidence Store
        </div>
      </footer>
    </div>
  );
};

export default App;

