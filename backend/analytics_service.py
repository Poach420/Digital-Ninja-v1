"""
Analytics and Monitoring Service
Track app usage, performance metrics, user behavior
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Track analytics and metrics for deployed apps"""
    
    def __init__(self, db):
        self.db = db
        self.analytics_collection = db.analytics
        self.metrics_collection = db.metrics
    
    async def track_event(
        self,
        project_id: str,
        event_type: str,
        data: Dict,
        user_id: Optional[str] = None
    ) -> bool:
        """Track an analytics event"""
        try:
            event_doc = {
                "project_id": project_id,
                "event_type": event_type,
                "data": data,
                "user_id": user_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc)
            }
            
            await self.analytics_collection.insert_one(event_doc)
            return True
        
        except Exception as e:
            logger.error(f"Failed to track event: {e}")
            return False
    
    async def get_project_analytics(
        self,
        project_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Get analytics for a project"""
        try:
            # Default to last 30 days
            if not start_date:
                start_date = datetime.now(timezone.utc) - timedelta(days=30)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            # Query events
            query = {
                "project_id": project_id,
                "created_at": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }
            
            events = await self.analytics_collection.find(query).to_list(length=10000)
            
            # Aggregate statistics
            stats = {
                "total_events": len(events),
                "unique_users": len(set(e.get("user_id") for e in events if e.get("user_id"))),
                "event_types": {},
                "daily_events": {},
                "peak_hours": [0] * 24
            }
            
            for event in events:
                # Count by event type
                event_type = event.get("event_type", "unknown")
                stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
                
                # Count by day
                date_str = event.get("timestamp", "")[:10]  # YYYY-MM-DD
                stats["daily_events"][date_str] = stats["daily_events"].get(date_str, 0) + 1
                
                # Track peak hours
                try:
                    hour = datetime.fromisoformat(event.get("timestamp", "")).hour
                    stats["peak_hours"][hour] += 1
                except:
                    pass
            
            return {
                "project_id": project_id,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "stats": stats
            }
        
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {"error": str(e)}
    
    async def track_performance_metric(
        self,
        project_id: str,
        metric_name: str,
        value: float,
        unit: str = "ms"
    ) -> bool:
        """Track a performance metric"""
        try:
            metric_doc = {
                "project_id": project_id,
                "metric_name": metric_name,
                "value": value,
                "unit": unit,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "created_at": datetime.now(timezone.utc)
            }
            
            await self.metrics_collection.insert_one(metric_doc)
            return True
        
        except Exception as e:
            logger.error(f"Failed to track metric: {e}")
            return False
    
    async def get_performance_metrics(
        self,
        project_id: str,
        metric_name: Optional[str] = None,
        hours: int = 24
    ) -> Dict:
        """Get performance metrics for a project"""
        try:
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            query = {
                "project_id": project_id,
                "created_at": {"$gte": start_time}
            }
            
            if metric_name:
                query["metric_name"] = metric_name
            
            metrics = await self.metrics_collection.find(query).to_list(length=10000)
            
            # Aggregate by metric name
            aggregated = {}
            for metric in metrics:
                name = metric.get("metric_name", "unknown")
                value = metric.get("value", 0)
                
                if name not in aggregated:
                    aggregated[name] = {
                        "values": [],
                        "min": value,
                        "max": value,
                        "unit": metric.get("unit", "")
                    }
                
                aggregated[name]["values"].append(value)
                aggregated[name]["min"] = min(aggregated[name]["min"], value)
                aggregated[name]["max"] = max(aggregated[name]["max"], value)
            
            # Calculate averages
            for name, data in aggregated.items():
                if data["values"]:
                    data["avg"] = sum(data["values"]) / len(data["values"])
                    data["count"] = len(data["values"])
            
            return {
                "project_id": project_id,
                "period_hours": hours,
                "metrics": aggregated
            }
        
        except Exception as e:
            logger.error(f"Failed to get metrics: {e}")
            return {"error": str(e)}
    
    async def get_dashboard_data(self, project_id: str) -> Dict:
        """Get comprehensive dashboard data"""
        try:
            # Get analytics for last 7 days
            analytics = await self.get_project_analytics(
                project_id,
                start_date=datetime.now(timezone.utc) - timedelta(days=7)
            )
            
            # Get performance metrics for last 24 hours
            performance = await self.get_performance_metrics(project_id, hours=24)
            
            # Get recent errors (if any tracked)
            recent_errors = await self.analytics_collection.find({
                "project_id": project_id,
                "event_type": "error",
                "created_at": {"$gte": datetime.now(timezone.utc) - timedelta(hours=24)}
            }).sort("created_at", -1).limit(10).to_list(length=10)
            
            return {
                "project_id": project_id,
                "analytics": analytics,
                "performance": performance,
                "recent_errors": recent_errors,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        
        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {"error": str(e)}
