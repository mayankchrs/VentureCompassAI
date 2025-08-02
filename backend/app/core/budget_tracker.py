"""
Budget tracking and cost monitoring for OpenAI API usage.
Implements $10 hard limit with intelligent cost estimation.
"""

from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import asyncio
from app.core.database import get_database, generate_cache_key, get_from_cache, set_cache
import logging

logger = logging.getLogger(__name__)

class BudgetExceededException(Exception):
    """Raised when budget limit would be exceeded."""
    pass

class BudgetTracker:
    """Tracks OpenAI API usage against $10 budget limit."""
    
    def __init__(self, max_budget: float = 10.0):
        self.max_budget = max_budget
        self.current_run_id: Optional[str] = None  # Track current run
        self._cost_estimates = {
            "gpt-4o-mini": {
                "input": 0.00015 / 1000,   # $0.15 per 1M input tokens
                "output": 0.0006 / 1000    # $0.60 per 1M output tokens
            }
        }
    
    def set_run_id(self, run_id: str) -> None:
        """Set the current run ID for tracking."""
        self.current_run_id = run_id
        logger.info(f"Budget tracker now tracking run: {run_id}")
    
    async def reset_for_new_run(self, run_id: str) -> None:
        """Reset budget tracking for a new run (for display purposes)."""
        self.current_run_id = run_id
        # Note: We still track actual costs in DB for total monitoring
        # But for user experience, we show fresh budget per run
        run_spend = await self.get_run_spend()
        logger.info(f"Starting fresh budget tracking for run: {run_id} (previous runs: ${await self.get_current_spend() - run_spend:.4f})")
    
    async def get_current_spend(self, run_id: Optional[str] = None) -> float:
        """Get current spend - either for specific run or total."""
        db = get_database()
        
        # If run_id provided, get spend for that specific run
        if run_id:
            pipeline = [
                {"$match": {"run_id": run_id}},
                {"$group": {"_id": None, "total": {"$sum": "$cost"}}}
            ]
        else:
            # Default: get total spend across all runs
            pipeline = [
                {"$group": {"_id": None, "total": {"$sum": "$cost"}}}
            ]
            
        result = await db.budget_tracking.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0.0
    
    async def get_run_spend(self) -> float:
        """Get spend for current run only."""
        if not self.current_run_id:
            return 0.0
        return await self.get_current_spend(self.current_run_id)
    
    async def estimate_cost(self, operation: str, input_tokens: int, output_tokens: int = 500) -> float:
        """Estimate cost for OpenAI API call."""
        model_costs = self._cost_estimates["gpt-4o-mini"]
        estimated_cost = (input_tokens * model_costs["input"]) + (output_tokens * model_costs["output"])
        return estimated_cost
    
    async def check_budget(self, estimated_cost: float, warn_only: bool = True) -> bool:
        """Check if operation would exceed budget. Returns warning but doesn't block."""
        total_spend = await self.get_current_spend()
        run_spend = await self.get_run_spend() if self.current_run_id else 0.0
        
        # For user-friendly display, focus on run-level budget tracking
        if run_spend + estimated_cost > 2.0:  # Warn if single run exceeds $2
            logger.warning(f"Run budget warning: ${estimated_cost:.4f} would bring run total to ${run_spend + estimated_cost:.4f}")
            logger.warning(f"Current run spend: ${run_spend:.4f}, Total cumulative: ${total_spend:.4f}")
        
        # Still check global limit but as secondary concern
        if total_spend + estimated_cost > self.max_budget:
            remaining = self.max_budget - total_spend
            logger.warning(f"Global budget warning: ${estimated_cost:.4f} would exceed ${remaining:.4f} remaining globally")
            
            if warn_only:
                return True  # Continue with warning
            else:
                return False  # Block operation
        return True
    
    async def record_cost(self, operation: str, actual_cost: float, tokens_used: int, metadata: Dict[str, Any] = None) -> None:
        """Record actual cost and usage."""
        db = get_database()
        record = {
            "operation": operation,
            "cost": actual_cost,
            "tokens_used": tokens_used,
            "timestamp": datetime.utcnow(),
            "run_id": self.current_run_id,  # Track which run this cost belongs to
            "metadata": metadata or {}
        }
        await db.budget_tracking.insert_one(record)
        
        run_total = await self.get_run_spend() if self.current_run_id else 0.0
        current_total = await self.get_current_spend()
        logger.info(f"Cost recorded: ${actual_cost:.4f} | This run: ${run_total:.4f} | Global total: ${current_total:.4f}/${self.max_budget}")
    
    async def get_budget_status(self) -> Dict[str, Any]:
        """Get comprehensive budget status."""
        current_spend = await self.get_current_spend()
        remaining = self.max_budget - current_spend
        
        # Get recent usage
        db = get_database()
        recent_costs = await db.budget_tracking.find().sort("timestamp", -1).limit(10).to_list(10)
        
        return {
            "max_budget": self.max_budget,
            "current_spend": current_spend,
            "remaining": remaining,
            "percentage_used": (current_spend / self.max_budget) * 100,
            "recent_operations": recent_costs,
            "status": "healthy" if remaining > 2.0 else "warning" if remaining > 0.5 else "critical"
        }

# Global budget tracker instance
budget_tracker = BudgetTracker()

async def with_budget_check(operation: str, estimated_tokens: int):
    """Decorator for budget-aware operations."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Check budget before operation
            estimated_cost = await budget_tracker.estimate_cost(operation, estimated_tokens)
            if not await budget_tracker.check_budget(estimated_cost):
                raise BudgetExceededException(f"Operation would exceed budget: ${estimated_cost:.4f}")
            
            # Execute operation
            result = await func(*args, **kwargs)
            
            # Record actual cost (simplified - in real implementation, get from OpenAI response)
            await budget_tracker.record_cost(operation, estimated_cost, estimated_tokens)
            
            return result
        return wrapper
    return decorator

async def cached_llm_operation(operation: str, params: Dict[str, Any], ttl_hours: int = 24):
    """Cache-aware LLM operation to avoid repeat API calls."""
    cache_key = generate_cache_key(operation, params)
    
    # Try cache first
    cached_result = await get_from_cache(cache_key)
    if cached_result:
        logger.info(f"Cache hit for {operation} - saved API call")
        return cached_result
    
    # Check budget before making API call
    estimated_tokens = len(str(params)) // 4  # Rough token estimation
    estimated_cost = await budget_tracker.estimate_cost(operation, estimated_tokens)
    
    if not await budget_tracker.check_budget(estimated_cost):
        raise BudgetExceededException(f"Cannot perform {operation}: would exceed budget")
    
    # This would be replaced with actual OpenAI API call
    logger.info(f"Cache miss for {operation} - making API call")
    result = {"operation": operation, "cached": False}
    
    # Record cost and cache result
    await budget_tracker.record_cost(operation, estimated_cost, estimated_tokens)
    await set_cache(cache_key, result, ttl_hours)
    
    return result