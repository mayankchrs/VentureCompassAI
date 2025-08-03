import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { RunCreateRequest, RunState, BudgetStatus, RunsHistoryResponse } from '@/types/api';

export function useCreateRun() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: RunCreateRequest) => apiClient.createRun(data),
    onSuccess: () => {
      // Invalidate budget status to refresh it after creating a run
      queryClient.invalidateQueries({ queryKey: ['budget'] });
    },
  });
}

export function useRunStatus(runId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: ['run', runId],
    queryFn: () => apiClient.getRun(runId!),
    enabled: enabled && !!runId,
    refetchInterval: (query) => {
      const data = query.state.data;
      // Stop polling if run is complete or errored
      if (!data || data.status === 'complete' || data.status === 'completed' || data.status === 'error') {
        return false;
      }
      // Poll every 2 seconds for running/pending runs
      return 2000;
    },
    refetchIntervalInBackground: true,
  });
}

export function useBudgetStatus() {
  return useQuery({
    queryKey: ['budget'],
    queryFn: () => apiClient.getBudgetStatus(),
    refetchInterval: 5000, // Refresh budget every 5 seconds
    refetchIntervalInBackground: true,
  });
}

export function useExportRun(runId: string | null) {
  return useQuery({
    queryKey: ['export', runId],
    queryFn: () => apiClient.exportRun(runId!),
    enabled: false, // Only run when explicitly triggered
  });
}

export function useRunsHistory() {
  return useQuery({
    queryKey: ['runs-history'],
    queryFn: () => apiClient.getRunsHistory(),
    refetchInterval: 30000, // Refresh every 30 seconds
    refetchIntervalInBackground: false,
  });
}