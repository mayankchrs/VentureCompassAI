'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Search, Building2, Globe } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useCreateRun } from '@/hooks/useRunAnalysis';

interface CompanySearchFormProps {
  onRunCreated: (runId: string) => void;
}

export function CompanySearchForm({ onRunCreated }: CompanySearchFormProps) {
  const [company, setCompany] = useState('');
  const [domain, setDomain] = useState('');
  const createRunMutation = useCreateRun();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company.trim()) return;

    try {
      const result = await createRunMutation.mutateAsync({
        company: company.trim(),
        domain: domain.trim() || undefined,
      });
      onRunCreated(result.run_id);
    } catch (error) {
      console.error('Failed to create run:', error);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full max-w-2xl mx-auto"
    >
      <Card className="border-2 border-dashed border-primary/20 hover:border-primary/40 transition-colors">
        <CardHeader className="text-center">
          <CardTitle className="text-3xl font-bold bg-gradient-to-r from-primary to-purple-600 bg-clip-text text-transparent">
            VentureCompass AI
          </CardTitle>
          <CardDescription className="text-lg">
            AI-powered startup intelligence with 8-agent multi-phase analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="company" className="text-sm font-medium flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                Company Name *
              </label>
              <Input
                id="company"
                type="text"
                placeholder="e.g., Notion, Stripe, Anthropic"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="text-lg"
                required
              />
            </div>
            
            <div className="space-y-2">
              <label htmlFor="domain" className="text-sm font-medium flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Website Domain (optional)
              </label>
              <Input
                id="domain"
                type="text"
                placeholder="e.g., notion.so, stripe.com"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
              />
            </div>

            <motion.div
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <Button
                type="submit"
                className="w-full text-lg py-6"
                disabled={createRunMutation.isPending || !company.trim()}
              >
                {createRunMutation.isPending ? (
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="mr-2"
                  >
                    <Search className="h-5 w-5" />
                  </motion.div>
                ) : (
                  <Search className="h-5 w-5 mr-2" />
                )}
                {createRunMutation.isPending ? 'Starting Analysis...' : 'Start AI Analysis'}
              </Button>
            </motion.div>
          </form>

          <div className="mt-6 text-center text-sm text-muted-foreground">
            <p>
              ✨ Complete Tavily API integration • 🤖 8-agent LangGraph workflow • 💰 Budget-optimized
            </p>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}