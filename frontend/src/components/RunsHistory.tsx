'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { 
  Clock, 
  DollarSign, 
  AlertTriangle, 
  CheckCircle, 
  Loader2, 
  XCircle,
  Building2,
  Calendar,
  Eye
} from 'lucide-react';
import { useRunsHistory } from '@/hooks/useRunAnalysis';
import { RunHistoryItem, RunStatus } from '@/types/api';

const statusConfig: Record<RunStatus, { icon: React.ReactNode; color: string; label: string }> = {
  pending: { icon: <Clock className="h-4 w-4" />, color: 'text-yellow-600', label: 'Pending' },
  running: { icon: <Loader2 className="h-4 w-4 animate-spin" />, color: 'text-blue-600', label: 'Running' },
  partial: { icon: <AlertTriangle className="h-4 w-4" />, color: 'text-orange-600', label: 'Partial' },
  complete: { icon: <CheckCircle className="h-4 w-4" />, color: 'text-green-600', label: 'Complete' },
  completed: { icon: <CheckCircle className="h-4 w-4" />, color: 'text-green-600', label: 'Complete' },
  error: { icon: <XCircle className="h-4 w-4" />, color: 'text-red-600', label: 'Error' },
};

interface RunsHistoryProps {
  onSelectRun?: (runId: string) => void;
}

export function RunsHistory({ onSelectRun }: RunsHistoryProps) {
  const { data: historyData, isLoading, error, refetch } = useRunsHistory();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(4)}`;
  };

  const handleViewRun = (runId: string) => {
    if (onSelectRun) {
      onSelectRun(runId);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Analysis History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Loading history...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Analysis History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <XCircle className="h-8 w-8 text-red-500 mx-auto mb-2" />
            <p className="text-muted-foreground mb-4">Failed to load history</p>
            <Button onClick={() => refetch()} variant="outline" size="sm">
              Try Again
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  const runs = historyData?.runs || [];

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Building2 className="h-5 w-5" />
          Analysis History
          <Badge variant="secondary" className="ml-auto">
            {runs.length} runs
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {runs.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Building2 className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium mb-2">No analysis runs yet</p>
            <p className="text-sm">Start your first company analysis to see it here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {runs.map((run, index) => {
              const status = statusConfig[run.status];
              return (
                <motion.div
                  key={run.run_id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="border-2 hover:border-primary/50 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h4 className="font-semibold text-lg">{run.company.name}</h4>
                            <Badge variant="outline" className={`${status.color} border-current`}>
                              {status.icon}
                              <span className="ml-1">{status.label}</span>
                            </Badge>
                          </div>
                          
                          {run.company.domain && (
                            <p className="text-sm text-muted-foreground mb-3">
                              🌐 {run.company.domain}
                            </p>
                          )}

                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div className="flex items-center gap-1">
                              <Calendar className="h-4 w-4 text-muted-foreground" />
                              <span className="text-muted-foreground">Created:</span>
                              <span className="font-medium">{formatDate(run.created_at)}</span>
                            </div>
                            
                            {run.duration_minutes && (
                              <div className="flex items-center gap-1">
                                <Clock className="h-4 w-4 text-muted-foreground" />
                                <span className="text-muted-foreground">Duration:</span>
                                <span className="font-medium">{run.duration_minutes}m</span>
                              </div>
                            )}
                            
                            <div className="flex items-center gap-1">
                              <DollarSign className="h-4 w-4 text-muted-foreground" />
                              <span className="text-muted-foreground">Cost:</span>
                              <span className="font-medium">{formatCost(run.estimated_total_cost_usd)}</span>
                            </div>
                            
                            {run.error_count > 0 && (
                              <div className="flex items-center gap-1">
                                <AlertTriangle className="h-4 w-4 text-orange-500" />
                                <span className="text-muted-foreground">Errors:</span>
                                <span className="font-medium text-orange-600">{run.error_count}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex flex-col gap-2 ml-4">
                          <Button
                            onClick={() => handleViewRun(run.run_id)}
                            size="sm"
                            className="min-w-[100px]"
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            View
                          </Button>
                          <Badge variant="outline" className="text-xs justify-center">
                            {run.run_id}
                          </Badge>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
            
            {historyData?.page_info.has_more && (
              <div className="text-center pt-4">
                <Button variant="outline" onClick={() => refetch()}>
                  Load More
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}