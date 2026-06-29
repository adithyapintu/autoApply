export type AutomationTask = {
  applicationId: string;
  targetUrl: string;
  siteAdapter: string;
  answers: Record<string, string>;
  files: Record<string, string>;
};

export type ApprovalCheckpoint = {
  summary: Record<string, unknown>;
  screenshotPath?: string;
  submitSelector: string;
};

export interface SiteAdapter {
  name: string;
  fillUntilApproval(task: AutomationTask): Promise<ApprovalCheckpoint>;
  submitAfterApproval(task: AutomationTask, checkpoint: ApprovalCheckpoint): Promise<void>;
}

