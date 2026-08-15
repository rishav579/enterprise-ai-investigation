import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { QuestionInput } from '../components/QuestionInput';
import { mockScenarioList } from './mockData';

describe('QuestionInput component', () => {
  it('renders question input and character counter', () => {
    render(
      <QuestionInput
        question="Why did churn increase?"
        onChangeQuestion={vi.fn()}
        onRunInvestigation={vi.fn()}
        onReset={vi.fn()}
        isLoading={false}
        scenarios={mockScenarioList}
        selectedScenarioId="scenario_A_churn"
        onSelectScenario={vi.fn()}
        isBackendOnline={true}
      />
    );

    const textarea = screen.getByDisplayValue('Why did churn increase?');
    expect(textarea).toBeInTheDocument();
    expect(screen.getByText('23/1000 chars')).toBeInTheDocument();
  });

  it('renders preset scenario buttons and selects scenario', () => {
    const handleSelect = vi.fn();
    render(
      <QuestionInput
        question=""
        onChangeQuestion={vi.fn()}
        onRunInvestigation={vi.fn()}
        onReset={vi.fn()}
        isLoading={false}
        scenarios={mockScenarioList}
        selectedScenarioId=""
        onSelectScenario={handleSelect}
        isBackendOnline={true}
      />
    );

    expect(screen.getByText('Q3 Customer')).toBeInTheDocument();
    const btn = screen.getByText('Q3 Customer');
    fireEvent.click(btn);
    expect(handleSelect).toHaveBeenCalledWith(mockScenarioList[0]);
  });

  it('dispatches onRunInvestigation on submit when valid and online', () => {
    const handleRun = vi.fn();
    render(
      <QuestionInput
        question="Valid test inquiry about billing failures"
        onChangeQuestion={vi.fn()}
        onRunInvestigation={handleRun}
        onReset={vi.fn()}
        isLoading={false}
        scenarios={mockScenarioList}
        selectedScenarioId="scenario_A_churn"
        onSelectScenario={vi.fn()}
        isBackendOnline={true}
      />
    );

    const runBtn = screen.getByRole('button', { name: /run investigation/i });
    expect(runBtn).not.toBeDisabled();
    fireEvent.click(runBtn);
    expect(handleRun).toHaveBeenCalledTimes(1);
  });

  it('disables run button when backend is offline', () => {
    render(
      <QuestionInput
        question="Valid test question"
        onChangeQuestion={vi.fn()}
        onRunInvestigation={vi.fn()}
        onReset={vi.fn()}
        isLoading={false}
        scenarios={mockScenarioList}
        selectedScenarioId=""
        onSelectScenario={vi.fn()}
        isBackendOnline={false}
      />
    );

    const runBtn = screen.getByRole('button', { name: /run investigation/i });
    expect(runBtn).toBeDisabled();
    expect(screen.getByText(/backend is offline/i)).toBeInTheDocument();
  });
});
